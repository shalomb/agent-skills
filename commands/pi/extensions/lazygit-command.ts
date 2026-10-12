/**
 * /lazygit and /lg — open lazygit in a blocking tmux popup directly from the
 * extension. No agent turn, no tokens: the command handler spawns tmux itself.
 * Args are forwarded to lazygit (e.g. `status`, `branch`, `log`, `stash`, `-f <path>`).
 *
 * `/lazygit diff` is a review mode: Files panel, narrow list + wide diff pane, 98% popup.
 * It layers a temporary overlay config (mkdtemp, removed after the popup) over the
 * user's lazygit config.yml, so it needs no extra files on disk.
 *
 * Hand-maintained: this file is NOT generated from commands.json. Do not run
 * tools/generate_commands.py --clean without excluding it (it would be removed as an orphan).
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

const DIFF_OVERLAY = "gui:\n  sidePanelWidth: 0.2\n  screenMode: half\n";

export default function (pi: ExtensionAPI) {
  const run = async (args: string, ctx: any) => {
    const notify = (m: string, l: "info" | "warning" | "error" = "info") => ctx.ui.notify(m, l);
    if (!process.env.TMUX) return notify("/lazygit needs a tmux session (popup).", "error");

    const git = (a: string[]) => pi.exec("git", ["-C", ctx.cwd, ...a], { timeout: 5000 });
    const root = await git(["rev-parse", "--show-toplevel"]);
    if (root.code !== 0) return notify(`Not a git repository: ${ctx.cwd}`, "error");
    const repoRoot = root.stdout.trim();

    const br = await git(["rev-parse", "--abbrev-ref", "HEAD"]);
    let branch = br.stdout.trim() || "HEAD";
    if (branch === "HEAD") {
      const sha = await git(["rev-parse", "--short", "HEAD"]);
      branch = `detached:${sha.stdout.trim()}`;
    }
    const repoName = repoRoot.split("/").pop();
    let extra = args.trim() ? args.trim().split(/\s+/) : [];

    // `/lazygit diff`: Files panel, narrow list + wide diff pane, near-full-screen popup.
    const diffMode = extra[0] === "diff";
    let tmpDir: string | undefined;
    try {
      if (diffMode) {
        tmpDir = mkdtempSync(join(tmpdir(), "pi-lazygit-"));
        const overlay = join(tmpDir, "diff.yml");
        writeFileSync(overlay, DIFF_OVERLAY);
        const userCfg = join(process.env.XDG_CONFIG_HOME || join(homedir(), ".config"), "lazygit", "config.yml");
        const cfgs = existsSync(userCfg) ? [userCfg, overlay] : [overlay];
        extra = ["-ucf", cfgs.join(","), "-sm", "half", "status", ...extra.slice(1)];
      }
      const size = diffMode ? "98%" : "90%";

      const res = await pi.exec("tmux", [
        "display-popup", "-E", "-d", repoRoot, "-w", size, "-h", size,
        "-T", ` Lazygit: ${repoName} (${branch}) `, "lazygit", ...extra,
      ]);
      if (res.code !== 0) return notify(`lazygit popup failed (${res.code}): ${res.stderr.trim() || "is lazygit installed?"}`, "error");
    } finally {
      if (tmpDir) rmSync(tmpDir, { recursive: true, force: true });
    }

    const st = await git(["status", "--short"]);
    const lines = st.stdout.split("\n").filter(Boolean);
    notify(lines.length ? `lazygit closed — ${lines.length} uncommitted change(s) in ${repoName}` : `lazygit closed — ${repoName} clean`);
  };

  for (const name of ["lazygit", "lg"]) {
    pi.registerCommand(name, {
      description: "Open lazygit in a tmux popup (no agent turn). `diff` = review layout. Args forwarded to lazygit.",
      handler: run,
    });
  }
}
