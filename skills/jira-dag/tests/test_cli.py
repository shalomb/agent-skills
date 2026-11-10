import os, subprocess, sys, unittest

S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, os.path.join(S, "po_view.py"), *args], capture_output=True, text=True)

    def test_story_view_is_retired(self):
        r = self.run_cli("--synthetic", "--epic", "PLT-10", "--outdir", "/tmp/jira-dag-cli-test")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unrecognized arguments: --epic", r.stderr)

    def test_help_does_not_mention_story_view(self):
        self.assertNotIn("story", self.run_cli("--help").stdout.lower())


if __name__ == "__main__":
    unittest.main()
