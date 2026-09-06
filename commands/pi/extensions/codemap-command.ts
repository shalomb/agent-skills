/**
 * Codemap Architecture Explorer Command Extension for Pi
 * Registers `/codemap` to map codebase architecture, dependency flow, hub files, and blast radius.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("codemap", {
    description: "Map codebase architecture, dependency flow, hub files, and blast radius",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:codemap ${query}`
        : "/skill:codemap Please assist with mapping codebase dependencies and architecture.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Codemap Architecture Explorer task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
