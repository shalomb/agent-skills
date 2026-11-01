/**
 * /understand — Navigate repository structure, topics, pull requests, and diffs.
 * Registered commands: /understand, /understand-pr, /understand-diff.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { execFile, spawn } from "node:child_process";
import { resolve } from "node:path";
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

export async function executePythonRunner(
  args: string,
  cwd: string,
  onPhase?: (phase: string) => void
): Promise<{ runDir: string; urls: ReportUrls; endMessage: string }> {
  const runnerScript = resolve(
    __dirname,
    "../../skills/understand/scripts"
  );

  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(
      "python3",
      ["-m", "understand_runs.cli", "--json", "--cwd", cwd, ...args.trim().split(/\s+/).filter(Boolean)],
      {
        cwd,
        env: {
          ...process.env,
          PYTHONPATH: runnerScript,
        },
      }
    );

    let stdoutData = "";
    let stderrData = "";

    child.stdout.on("data", (chunk: Buffer) => {
      const text = chunk.toString();
      stdoutData += text;
      const lines = text.split("\n");
      for (const line of lines) {
        if (line.startsWith("PHASE:")) {
          const phase = line.replace("PHASE:", "").trim();
          onPhase?.(phase);
        }
      }
    });

    child.stderr.on("data", (chunk: Buffer) => {
      stderrData += chunk.toString();
    });

    child.on("close", (code) => {
      if (code !== 0) {
        return rejectPromise(
          new Error(stderrData.trim() || `Runner exited with code ${code}`)
        );
      }

      // Look for JSON payload in stdout
      const lines = stdoutData.trim().split("\n");
      let parsedJson: any = null;
      for (let i = lines.length - 1; i >= 0; i--) {
        const line = lines[i].trim();
        if (line.startsWith("{") && line.endsWith("}")) {
          try {
            parsedJson = JSON.parse(line);
            break;
          } catch {
            // continue looking
          }
        }
      }

      if (!parsedJson) {
        return rejectPromise(
          new Error(`Failed to parse runner output: ${stdoutData}`)
        );
      }

      resolvePromise({
        runDir: parsedJson.run_dir,
        urls: parsedJson.urls,
        endMessage: parsedJson.end_message,
      });
    });
  });
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

  const onPhase = (phase: string) => {
    if (ctx.ui?.setStatus) {
      ctx.ui.setStatus("understand", phase);
    }
  };

  // If a custom runner is injected or available, run it
  const runner = ctx.runner || (ctx.executeRunner ? executePythonRunner : undefined);
  if (runner) {
    try {
      const runnerRes = await runner(args, cwd, onPhase);
      if (ctx.ui?.notify) {
        ctx.ui.notify(runnerRes.endMessage, "info");
      }
      return {
        success: true,
        lens,
        urls: runnerRes.urls,
        endMessage: runnerRes.endMessage,
      };
    } catch (err: any) {
      const errorMsg = err?.message || String(err);
      if (ctx.ui?.notify) {
        ctx.ui.notify(`Report failed: ${errorMsg}`, "error");
      }
      return { success: false, error: errorMsg };
    }
  }

  // Fallback / fast progress notification for mock/test runs without runner
  const phases = ["plan", "discover", "converge", "render"];
  for (const phase of phases) {
    onPhase(phase);
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
      await runUnderstand(args, { ...ctx, executeRunner: true });
    },
    getArgumentCompletions: (prefix: string) => getArgumentCompletions(prefix),
  };

  pi.registerCommand("understand", understandSpec);

  pi.registerCommand("understand-pr", {
    description: "Inspect a pull request report (alias for /understand pr <arg>)",
    handler: async (args: string, ctx: any) => {
      await runUnderstand(`pr ${args}`.trim(), { ...ctx, executeRunner: true });
    },
  });

  pi.registerCommand("understand-diff", {
    description: "Inspect a diff report (alias for /understand diff <arg>)",
    handler: async (args: string, ctx: any) => {
      await runUnderstand(`diff ${args}`.trim(), { ...ctx, executeRunner: true });
    },
  });
}
