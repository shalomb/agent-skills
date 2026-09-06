/**
 * C4 Architecture Diagrams Command Extension for Pi
 * Registers `/c4` to generate software architecture documentation using c4 model mermaid diagrams.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("c4", {
    description: "Generate software architecture documentation using C4 model Mermaid diagrams",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:c4-architecture ${query}`
        : "/skill:c4-architecture Please assist with generating C4 architecture diagrams.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("C4 Architecture Diagrams task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
