/**
 * Test Design Review Command Extension for Pi
 * Registers `/test-review` to critique tests or diffs against dave farley's properties of good tests and gojko adzic's bdd principles.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("test-review", {
    description: "Critique tests or diffs against Dave Farley's Properties of Good Tests and Gojko Adzic's BDD principles",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:test-design-review ${query}`
        : "/skill:test-design-review Please assist with reviewing test design and executable specifications.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Test Design Review task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
