/**
 * Adzic BDD Specification Command Extension for Pi
 * Registers `/bdd` to apply gojko adzic specification by example principles to feature files and user stories.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("bdd", {
    description: "Apply Gojko Adzic Specification by Example principles to feature files and user stories",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:adzic-bdd ${query}`
        : "/skill:adzic-bdd Please assist with refining BDD specifications and feature files.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Adzic BDD Specification task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
