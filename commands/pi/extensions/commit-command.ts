/**
 * Atomic Commit Protocol Command Extension for Pi
 * Registers `/commit` to structure and format git commits following the atomic commit protocol (acp).
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("commit", {
    description: "Structure and format git commits following the Atomic Commit Protocol (ACP)",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:git-commit-formatter ${query}`
        : "/skill:git-commit-formatter Please assist with formatting and staging an atomic commit.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Atomic Commit Protocol task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
