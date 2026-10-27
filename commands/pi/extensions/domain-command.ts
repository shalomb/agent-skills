/**
 * Domain Modeling & Ubiquitous Language Command Extension for Pi
 * Registers `/domain` to build and sharpen a project domain model, glossary.md, and bounded contexts.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("domain", {
    description: "Build and sharpen a project domain model, GLOSSARY.md, and bounded contexts",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:domain-modeling ${query}`
        : "/skill:domain-modeling Please assist with sharpening domain terminology and updating GLOSSARY.md.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Domain Modeling & Ubiquitous Language task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
