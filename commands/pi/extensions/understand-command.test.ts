import { describe, expect, test } from "bun:test";
import registerUnderstandExtension, {
  formatEndMessage,
  getArgumentCompletions,
  getReportUrls,
  parseCommand,
  runUnderstand,
  type Lens,
} from "./understand-command.ts";

describe("parseCommand", () => {
  test("parses full command with no args", () => {
    expect(parseCommand("/understand")).toEqual({ type: "full" });
    expect(parseCommand("/understand ")).toEqual({ type: "full" });
    expect(parseCommand("")).toEqual({ type: "full" });
  });

  test("parses topic lens", () => {
    expect(parseCommand("/understand onboarding")).toEqual({
      type: "topic",
      target: "onboarding",
    });
    expect(parseCommand("onboarding")).toEqual({
      type: "topic",
      target: "onboarding",
    });
  });

  test("parses pr subcommand and short alias identically", () => {
    const fromSub = parseCommand("/understand pr 123");
    const fromShort = parseCommand("/understand-pr 123");
    expect(fromSub).toEqual({ type: "pr", target: "123" });
    expect(fromShort).toEqual({ type: "pr", target: "123" });
    expect(fromShort).toEqual(fromSub);
  });

  test("parses diff subcommand and short alias identically", () => {
    const fromSub = parseCommand("/understand diff main");
    const fromShort = parseCommand("/understand-diff main");
    expect(fromSub).toEqual({ type: "diff", target: "main" });
    expect(fromShort).toEqual({ type: "diff", target: "main" });
    expect(fromShort).toEqual(fromSub);
  });
});

describe("getArgumentCompletions", () => {
  test("offers pr and diff for empty prefix", () => {
    const items = getArgumentCompletions("");
    const values = items?.map((i) => i.value);
    expect(values).toContain("pr");
    expect(values).toContain("diff");
  });

  test("filters by prefix", () => {
    const prItems = getArgumentCompletions("p");
    expect(prItems?.map((i) => i.value)).toEqual(["pr"]);

    const diffItems = getArgumentCompletions("d");
    expect(diffItems?.map((i) => i.value)).toEqual(["diff"]);
  });

  test("returns null for no matches", () => {
    expect(getArgumentCompletions("xyz")).toBeNull();
  });
});

describe("git vs non-git directory handling", () => {
  test("pr and diff fail in non-git directory", async () => {
    const mockCtx = {
      cwd: "/tmp/non-git-dir",
      isGitRepo: false,
      notifications: [] as string[],
      ui: {
        notify: (msg: string, level?: string) => {
          mockCtx.notifications.push(msg);
        },
        setStatus: (_id: string, _text: string) => {},
      },
    };

    const prResult = await runUnderstand("pr 1", mockCtx as any);
    expect(prResult.success).toBe(false);
    expect(prResult.error?.toLowerCase()).toContain(
      "a pull request report needs a git repository"
    );

    const diffResult = await runUnderstand("diff main", mockCtx as any);
    expect(diffResult.success).toBe(false);
    expect(diffResult.error?.toLowerCase()).toContain("needs a git repository");
  });

  test("full and topic succeed in non-git directory", async () => {
    const mockCtx = {
      cwd: "/tmp/non-git-dir",
      isGitRepo: false,
      notifications: [] as string[],
      ui: {
        notify: (msg: string) => mockCtx.notifications.push(msg),
        setStatus: () => {},
      },
    };

    const fullResult = await runUnderstand("", mockCtx as any);
    expect(fullResult.success).toBe(true);

    const topicResult = await runUnderstand("onboarding", mockCtx as any);
    expect(topicResult.success).toBe(true);
  });
});

describe("phases and end message", () => {
  test("emits plan, discover, converge, render phases", async () => {
    const phases: string[] = [];
    const mockCtx = {
      cwd: "/tmp/fake-repo",
      isGitRepo: true,
      ui: {
        setStatus: (_name: string, status: string) => {
          phases.push(status);
        },
        notify: () => {},
      },
    };

    const result = await runUnderstand("", mockCtx as any);
    expect(result.success).toBe(true);
    expect(phases).toEqual(["plan", "discover", "converge", "render"]);
  });

  test("executes runner when executeRunner is true", async () => {
    let executed = false;
    let phasesReceived: string[] = [];
    const mockRunner = async (_args: string, _cwd: string, onPhase?: (p: string) => void) => {
      executed = true;
      onPhase?.("plan");
      onPhase?.("discover");
      onPhase?.("converge");
      onPhase?.("render");
      return {
        runDir: "/tmp/fake-run",
        urls: {
          parallels: "http://10.211.55.3:8787/r/understand/test/full/run-1/",
          tailnet: "http://100.99.83.53:8787/r/understand/test/full/run-1/",
        },
        endMessage: "Report ready: test (full)\nSummary: Real summary",
      };
    };

    const mockCtx = {
      cwd: "/tmp/fake-repo",
      isGitRepo: true,
      runner: mockRunner,
      ui: {
        setStatus: (_name: string, status: string) => {
          phasesReceived.push(status);
        },
        notify: () => {},
      },
    };

    const result = await runUnderstand("", mockCtx as any);
    expect(executed).toBe(true);
    expect(result.success).toBe(true);
    expect(phasesReceived).toEqual(["plan", "discover", "converge", "render"]);
    expect(result.urls?.parallels).toBe("http://10.211.55.3:8787/r/understand/test/full/run-1/");
  });

  test("report URLs and end message length", () => {
    const urls = getReportUrls("my-repo", "full", "run-123");
    expect(urls.parallels).toBe(
      "http://10.211.55.3:8787/r/understand/my-repo/full/run-123/"
    );
    expect(urls.tailnet).toBe(
      "http://100.99.83.53:8787/r/understand/my-repo/full/run-123/"
    );

    const msg = formatEndMessage("my-repo", "full", urls, "Short summary.");
    const lines = msg.trim().split("\n");
    expect(lines.length).toBeLessThanOrEqual(5);
    expect(msg).toContain(urls.parallels);
    expect(msg).toContain(urls.tailnet);
  });
});

describe("extension registration", () => {
  test("registers understand, understand-pr, and understand-diff commands", () => {
    const registered: Record<string, any> = {};
    const mockPi = {
      registerCommand: (name: string, spec: any) => {
        registered[name] = spec;
      },
    };

    registerUnderstandExtension(mockPi as any);
    expect(registered["understand"]).toBeDefined();
    expect(registered["understand-pr"]).toBeDefined();
    expect(registered["understand-diff"]).toBeDefined();
  });
});
