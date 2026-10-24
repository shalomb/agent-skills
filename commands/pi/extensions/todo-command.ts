/**
 * Todo Navigator Command Extension for Pi
 * Registers `/todo` to navigate project tasks, inspect roadmap, and view or edit task cards in shadow cache.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("todo", {
    description: "Navigate project tasks, inspect roadmap, and view or edit task cards in shadow cache",
    handler: async (args, ctx) => {
      const query = args.trim();

      // No args: open the master TODO in nvim in a tmux split to the right (no agent turn).
      if (!query) {
        if (!process.env.TMUX) {
          ctx.ui.notify("/todo needs a tmux session for the split", "error");
          return;
        }
        const res = await pi.exec("tmux", [
          "split-window", "-h", "-c", ctx.cwd, "VISUAL=nvim EDITOR=nvim todo edit --no-popup",
        ]);
        if (res.code !== 0) {
          ctx.ui.notify(`todo split failed (${res.code}): ${res.stderr.trim()}`, "error");
        }
        return;
      }
      const message = `/skill:todo-navigator ${query}`;

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Todo Navigator task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
