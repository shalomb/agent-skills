/**
 * Tracer-Bullet Tickets Generator Command Extension for Pi
 * Registers `/tickets` to decompose plans or specs into tracer-bullet vertical slices with explicit blocking dag edges.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("tickets", {
    description: "Decompose plans or specs into tracer-bullet vertical slices with explicit blocking DAG edges",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:to-tickets ${query}`
        : "/skill:to-tickets Please assist with breaking down work into tracer-bullet tickets with dependency edges.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Tracer-Bullet Tickets Generator task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
