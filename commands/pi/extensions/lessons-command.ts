/**
 * Lessons Learned Retrospective Command Extension for Pi
 * Registers `/lessons` to extract software engineering principles, takeaways, and anti-patterns from recent commits or diffs.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("lessons", {
    description: "Extract software engineering principles, takeaways, and anti-patterns from recent commits or diffs",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:lessons-learned ${query}`
        : "/skill:lessons-learned Please assist with extracting software engineering lessons from recent work.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Lessons Learned Retrospective task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
