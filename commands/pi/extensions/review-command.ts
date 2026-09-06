/**
 * Bart Adversarial Code Reviewer Command Extension for Pi
 * Registers `/review` to critically review code, diffs, or pull requests for bugs, edge cases, and design flaws.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("review", {
    description: "Critically review code, diffs, or pull requests for bugs, edge cases, and design flaws",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:bart-adversarial-reviewer ${query}`
        : "/skill:bart-adversarial-reviewer Please assist with critically reviewing code or a pull request.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Bart Adversarial Code Reviewer task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
