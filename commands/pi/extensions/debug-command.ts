/**
 * Systematic Debugging Command Extension for Pi
 * Registers `/debug` to investigate and resolve bugs systematically with root cause analysis before proposing fixes.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("debug", {
    description: "Investigate and resolve bugs systematically with root cause analysis before proposing fixes",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:systematic-debugging ${query}`
        : "/skill:systematic-debugging Please assist with systematic root cause debugging.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Systematic Debugging task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
