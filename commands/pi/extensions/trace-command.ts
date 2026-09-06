/**
 * Macro-to-Micro Codebase Tracing Command Extension for Pi
 * Registers `/trace` to trace bugs and refactoring blast radius by chaining codemap, lsp, and ast-grep.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("trace", {
    description: "Trace bugs and refactoring blast radius by chaining Codemap, LSP, and AST-grep",
    handler: async (args, ctx) => {
      const query = args.trim();
      const message = query
        ? `/skill:macro-to-micro ${query}`
        : "/skill:macro-to-micro Please assist with tracing structural code dependencies and blast radius.";

      if (!ctx.isIdle()) {
        pi.sendUserMessage(message, { deliverAs: "followUp" });
        ctx.ui.notify("Macro-to-Micro Codebase Tracing task queued as follow-up", "info");
      } else {
        pi.sendUserMessage(message);
      }
    },
  });
}
