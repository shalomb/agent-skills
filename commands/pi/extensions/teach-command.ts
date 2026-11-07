/**
 * Teach Command Extension for Pi
 * Registers `/teach` to learn a topic over multiple sessions in a guided workspace (mission, resources, lessons, learning records).
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("teach", {
    description: "Learn a topic over multiple sessions in a guided workspace (mission, resources, lessons, learning records)",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:teach ${query}`
        : "/skill:teach Please assist with teaching the user a new skill or concept in a stateful teaching workspace.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Teach task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
