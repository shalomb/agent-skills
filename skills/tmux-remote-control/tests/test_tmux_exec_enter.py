"""tmux-exec.sh must survive a dropped Enter. Run: python3 -m unittest -v tests/test_tmux_exec_enter.py

A shim `tmux` on PATH swallows the FIRST `send-keys ... C-m` of the command payload
(the observed fault: text typed, Return lost, command never starts), then delegates.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "tmux-exec.sh"
REAL_TMUX = shutil.which("tmux")


@unittest.skipUnless(REAL_TMUX, "tmux not installed")
class DroppedEnterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tmux-exec-enter-")
        self.sock = os.path.join(self.tmp, "sock")
        self.shim_dir = os.path.join(self.tmp, "bin")
        os.mkdir(self.shim_dir)
        self.flag = os.path.join(self.tmp, "dropped")
        shim = Path(self.shim_dir, "tmux")
        # Drop one C-m that follows a multi-line payload (the `λ (` command), once.
        shim.write_text(f"""#!/usr/bin/env bash
if [[ "$*" == *"send-keys"* && "$*" == *" C-m" && ! -e {self.flag} && -e {self.tmp}/armed ]]; then
  : > {self.flag}; exit 0
fi
if [[ "$*" == *"send-keys"* && "$*" == *"λ ("* ]]; then : > {self.tmp}/armed; fi
exec {REAL_TMUX} "$@"
""")
        shim.chmod(0o755)
        self.t("new-session", "-d", "-s", "t", "-n", "main", "-x", "120", "-y", "40")
        self.t("new-window", "-d", "-t", "t", "-n", "work", "bash --norc --noprofile -i")
        self.t("new-window", "-d", "-t", "t", "-n", "agent")
        self.agent = self.t("display-message", "-p", "-t", "t:agent", "#{pane_id}").strip()
        self.addCleanup(lambda: (subprocess.run([REAL_TMUX, "-S", self.sock, "kill-server"],
                                                capture_output=True),
                                 shutil.rmtree(self.tmp, ignore_errors=True)))

    def t(self, *a):
        r = subprocess.run([REAL_TMUX, "-S", self.sock, "-f", "/dev/null", *a],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_command_runs_although_first_enter_is_dropped(self):
        env = {k: v for k, v in os.environ.items() if k not in ("TMUX", "TMUX_PANE")}
        env.update(TMUX=f"{self.sock},1,0", TMUX_PANE=self.agent,
                   PATH=f"{self.shim_dir}:{os.environ['PATH']}", TMPDIR=self.tmp)
        r = subprocess.run(["bash", str(SCRIPT), "-S", self.sock, "-t", "20", "t:work",
                            "echo hello-enter"], env=env, capture_output=True, text=True,
                           timeout=40)
        pane = subprocess.run([REAL_TMUX,"-S",self.sock,"capture-pane","-p","-t","t:work"],capture_output=True,text=True).stdout
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr + "\nPANE:\n" + pane + "\nSTATE:" + str(os.listdir(self.tmp+"/tmux-exec-state."+str(os.getuid()))))
        self.assertTrue(os.path.exists(self.flag), "shim never dropped an Enter (test invalid)")
        self.assertIn("hello-enter", r.stdout)


if __name__ == "__main__":
    unittest.main()
