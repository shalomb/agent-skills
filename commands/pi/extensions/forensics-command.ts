/**
 * Git Forensics & Code Archaeology Command Extension for Pi
 * Registers `/forensics` to diagnose codebase health, detect bug hotspots, churn, bus factor, and perform git pickaxe archaeology.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("forensics", {
    description: "Diagnose codebase health, detect bug hotspots, churn, bus factor, and perform git pickaxe archaeology",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:git-forensics ${query}`
        : "/skill:git-forensics Please assist with analyzing codebase health and git forensics.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Git Forensics & Code Archaeology task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
