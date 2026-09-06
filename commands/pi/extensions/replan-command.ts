/**
 * Todo Replanner & Bootstrapper Command Extension for Pi
 * Registers `/replan` to bootstrap task backlog or replan outstanding tasks with topological dag sorting and wsjf waves.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("replan", {
    description: "Bootstrap task backlog or replan outstanding tasks with topological DAG sorting and WSJF waves",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:todo-navigator ${query}`
        : "/skill:todo-navigator Please assist with bootstrapping or replanning the project task backlog.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Todo Replanner & Bootstrapper task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
