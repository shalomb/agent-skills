/**
 * /understand — Navigate repository structure, topics, pull requests, and diffs.
 * Registered commands: /understand, /understand-pr, /understand-diff.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export const DEFAULT_PORT = 8787;
export const DEFAULT_PARALLELS_IP = "10.211.55.3";
export const DEFAULT_TAILNET_IP = "100.99.83.53";

export interface Lens {
  type: "full" | "topic" | "pr" | "diff";
  target?: string;
}

export interface ReportUrls {
  parallels: string;
  tailnet: string;
}

export interface UnderstandResult {
  success: boolean;
  lens?: Lens;
  urls?: ReportUrls;
  endMessage?: string;
  error?: string;
}

export function parseCommand(commandOrArgs: string): Lens {
  let text = commandOrArgs.trim();
  if (text.startsWith("/understand-pr")) {
    const arg = text.slice("/understand-pr".length).trim();
    return { type: "pr", target: arg || undefined };
  }
  if (text.startsWith("/understand-diff")) {
    const arg = text.slice("/understand-diff".length).trim();
    return { type: "diff", target: arg || undefined };
  }
  if (text.startsWith("/understand")) {
    text = text.slice("/understand".length).trim();
  }

  if (!text) {
    return { type: "full" };
  }

  const parts = text.split(/\s+/);
  const sub = parts[0];
  const rest = parts.slice(1).join(" ").trim();

  if (sub === "pr") {
    return { type: "pr", target: rest || undefined };
  }
  if (sub === "diff") {
    return { type: "diff", target: rest || undefined };
  }
  return { type: "topic", target: text };
}

export function getArgumentCompletions(
  prefix: string
): { value: string; label: string }[] | null {
  const trimmed = prefix.trim();
  const choices = [
    { value: "pr", label: "pr" },
    { value: "diff", label: "diff" },
  ];
  if (!trimmed) {
    return choices;
  }
  const filtered = choices.filter((c) => c.value.startsWith(trimmed));
  return filtered.length > 0 ? filtered : null;
}

export function getReportUrls(
  repoSlug: string,
  lensId: string,
  runId: string,
  port: number = DEFAULT_PORT,
  parallelsIp: string = DEFAULT_PARALLELS_IP,
  tailnetIp: string = DEFAULT_TAILNET_IP
): ReportUrls {
  const path = `/r/understand/${repoSlug}/${lensId}/${runId}/`;
  return {
    parallels: `http://${parallelsIp}:${port}${path}`,
    tailnet: `http://${tailnetIp}:${port}${path}`,
  };
}

export function formatEndMessage(
  repoSlug: string,
  lensId: string,
  urls: ReportUrls,
  summary: string = "Report generated successfully."
): string {
  const firstLineSummary = summary.trim().split("\n")[0] || "Report generated.";
  return [
    `Report ready: ${repoSlug} (${lensId})`,
    `Parallels: ${urls.parallels}`,
    `Tailnet:   ${urls.tailnet}`,
    `Summary:   ${firstLineSummary}`,
  ].join("\n");
}

export function deriveRepoSlug(cwd: string): string {
  const raw = cwd.replace(/^\/+|\/+$/g, "").replace(/[\/\\:]+/g, "-");
  return raw.replace(/-+/g, "-") || "default-repo";
}

async function checkIsGitRepo(cwd: string, ctx?: any): Promise<boolean> {
  if (ctx && typeof ctx.isGitRepo === "boolean") {
    return ctx.isGitRepo;
  }
  try {
    const res = await execFileAsync(
      "git",
      ["rev-parse", "--is-inside-work-tree"],
      { cwd }
    );
    return res.stdout.trim() === "true";
  } catch {
    return false;
  }
}

export async function runUnderstand(
  args: string,
  ctx: any
): Promise<UnderstandResult> {
  const lens = parseCommand(args);
  const cwd = ctx.cwd || process.cwd();

  const isGit = await checkIsGitRepo(cwd, ctx);
  if ((lens.type === "pr" || lens.type === "diff") && !isGit) {
    const errorMsg =
      lens.type === "pr"
        ? "A pull request report needs a git repository"
        : "A diff report needs a git repository";
    if (ctx.ui?.notify) {
      ctx.ui.notify(errorMsg, "error");
    }
    return { success: false, error: errorMsg };
  }

  // Progress notification: phases plan, discover, converge, render
  const phases = ["plan", "discover", "converge", "render"];
  for (const phase of phases) {
    if (ctx.ui?.setStatus) {
      ctx.ui.setStatus("understand", phase);
    }
  }

  const slug = deriveRepoSlug(cwd);
  const lensId =
    lens.type === "full"
      ? "full"
      : lens.type === "topic"
      ? `topic-${lens.target || ""}`
      : `${lens.type}-${lens.target || ""}`;

  const runId = `run-${Date.now()}`;
  const urls = getReportUrls(slug, lensId, runId);
  const summary =
    lens.type === "topic"
      ? `Topic report on ${lens.target}.`
      : `Full overview of ${slug}.`;
  const endMessage = formatEndMessage(slug, lensId, urls, summary);

  if (ctx.ui?.notify) {
    ctx.ui.notify(endMessage, "info");
  }

  return {
    success: true,
    lens,
    urls,
    endMessage,
  };
}

export default function registerUnderstandExtension(pi: ExtensionAPI) {
  const understandSpec = {
    description: "Inspect repository structure, topics, pull requests, and diffs",
    handler: async (args: string, ctx: any) => {
      await runUnderstand(args, ctx);
    },
    getArgumentCompletions: (prefix: string) => getArgumentCompletions(prefix),
  };

  pi.registerCommand("understand", understandSpec);

  pi.registerCommand("understand-pr", {
    description: "Inspect a pull request report (alias for /understand pr <arg>)",
    handler: async (args: string, ctx: any) => {
      await runUnderstand(`pr ${args}`.trim(), ctx);
    },
  });

  pi.registerCommand("understand-diff", {
    description: "Inspect a diff report (alias for /understand diff <arg>)",
    handler: async (args: string, ctx: any) => {
      await runUnderstand(`diff ${args}`.trim(), ctx);
    },
  });
}
