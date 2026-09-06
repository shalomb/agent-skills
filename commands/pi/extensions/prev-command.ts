/**
 * Previous Work Recall Command Extension for Pi
 * Registers `/prev` to recall what was just worked on: 3-line factual summary of last completed task and git commit.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("prev", {
    description: "Recall what was just worked on: 3-line factual summary of last completed task and git commit",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:todo-navigator ${query}`
        : "/skill:todo-navigator Please assist with recalling the last completed work and git commit.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Previous Work Recall task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
