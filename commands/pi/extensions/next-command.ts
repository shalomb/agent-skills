/**
 * Next Task Selector Command Extension for Pi
 * Registers `/next` to select the next unblocked, highest-leverage task and page in its acceptance criteria card.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("next", {
    description: "Select the next unblocked, highest-leverage task and page in its acceptance criteria card",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:todo-navigator ${query}`
        : "/skill:todo-navigator Please assist with selecting the next actionable task.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Next Task Selector task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
