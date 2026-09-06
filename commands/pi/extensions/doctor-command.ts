/**
 * Branch & PR Doctor Command Extension for Pi
 * Registers `/doctor` to audit branch health, working tree cleanliness, conventional commits, local tests, github ci, and pr well-formedness.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("doctor", {
    description: "Audit branch health, working tree cleanliness, conventional commits, local tests, GitHub CI, and PR well-formedness",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:branch-doctor ${query}`
        : "/skill:branch-doctor Please assist with running a comprehensive branch and PR health check.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Branch & PR Doctor task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
