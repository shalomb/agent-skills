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
      const message = query
        ? `/skill:todo-navigator ${query}`
        : "/skill:todo-navigator Please assist with navigating project tasks and inspecting the roadmap.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Todo Navigator task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
