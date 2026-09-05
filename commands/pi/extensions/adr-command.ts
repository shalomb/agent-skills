/**
 * ADR Command Extension for Pi
 * Registers `/adr` to create, update, or review Architecture Decision Records.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("adr", {
    description: "Create or review an Architecture Decision Record (ADR)",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:architecture-decision-records ${query}`
        : "/skill:architecture-decision-records Please assist with creating or reviewing an Architecture Decision Record.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("ADR task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
