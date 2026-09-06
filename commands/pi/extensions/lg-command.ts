/**
 * Lazygit Shortcut Command Extension for Pi
 * Registers `/lg` to quick alias for /lazygit to launch lazygit in a blocking tmux popup.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("lg", {
    description: "Quick alias for /lazygit to launch lazygit in a blocking tmux popup",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:lazygit ${query}`
        : "/skill:lazygit Please assist with launching lazygit in a tmux popup to review work.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Lazygit Shortcut task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
