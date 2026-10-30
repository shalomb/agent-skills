// Config loader
export interface Config { port: number }

// padding 4
// padding 5
// padding 6
// padding 7
// padding 8
// padding 9
// padding 10
// padding 11
export function parseConfig(argv: string[]): Config {
  return { port: Number(argv[2] ?? 8080) };
}
