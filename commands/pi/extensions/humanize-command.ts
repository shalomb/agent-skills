/**
 * AI Text Humanizer Command Extension for Pi
 * Registers `/humanize` to review and remove signs of ai-generated writing from text, adrs, or docs.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("humanize", {
    description: "Review and remove signs of AI-generated writing from text, ADRs, or docs",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:ai-text-humanizer ${query}`
        : "/skill:ai-text-humanizer Please assist with reviewing and humanizing text.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("AI Text Humanizer task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
