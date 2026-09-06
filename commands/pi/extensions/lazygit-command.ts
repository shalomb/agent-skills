/**
 * Lazygit Tmux Reviewer Command Extension for Pi
 * Registers `/lazygit` to launch lazygit terminal ui in a blocking tmux popup to review, stage, and inspect git changes in the current agent repository and branch.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("lazygit", {
    description: "Launch lazygit terminal UI in a blocking tmux popup to review, stage, and inspect git changes in the current agent repository and branch",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:lazygit ${query}`
        : "/skill:lazygit Please assist with launching lazygit in a tmux popup to review work.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Lazygit Tmux Reviewer task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
