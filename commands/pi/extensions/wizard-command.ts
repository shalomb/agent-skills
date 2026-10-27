/**
 * Interactive Bash Wizard Generator Command Extension for Pi
 * Registers `/wizard` to generate an interactive bash wizard for human-only steps (oauth, ci secrets, cutover).
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("wizard", {
    description: "Generate an interactive bash wizard for human-only steps (OAuth, CI secrets, cutover)",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:wizard ${query}`
        : "/skill:wizard Please assist with scoping and authoring an interactive bash wizard.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Interactive Bash Wizard Generator task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
