/**
 * Deep Module Codebase Design Command Extension for Pi
 * Registers `/design-code` to design deep modules, narrow interfaces, and locate clean seams (ousterhout).
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("design-code", {
    description: "Design deep modules, narrow interfaces, and locate clean seams (Ousterhout)",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:codebase-design ${query}`
        : "/skill:codebase-design Please assist with designing or deepening module interfaces and locating seams.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Deep Module Codebase Design task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
