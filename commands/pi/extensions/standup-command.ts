/**
 * Daily Standup Planner Command Extension for Pi
 * Registers `/standup` to turn meeting transcripts into actionable daily plans, decisions, and issue updates.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("standup", {
    description: "Turn meeting transcripts into actionable daily plans, decisions, and issue updates",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:daily-standup ${query}`
        : "/skill:daily-standup Please assist with processing a standup meeting transcript.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Daily Standup Planner task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
