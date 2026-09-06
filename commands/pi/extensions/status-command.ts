/**
 * Daily Status Reporter Command Extension for Pi
 * Registers `/status` to generate a factual summary of recent git commits, prs, and assigned issues.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("status", {
    description: "Generate a factual summary of recent git commits, PRs, and assigned issues",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:daily-status ${query}`
        : "/skill:daily-status Please assist with gathering and reporting recent activity.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Daily Status Reporter task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
