// The Home strip: where requests are waiting, in four words. Pure. "Done" requests are not loaded on Home.
import type { Bucket } from "./flow";

export type PipeId = "questions" | "choose" | "approve" | "waiting";
export const PIPELINE: ReadonlyArray<{ id: PipeId; label: string; buckets: readonly Bucket[] }> = [
  { id: "questions", label: "Questions", buckets: ["answer", "confirm"] },
  { id: "choose", label: "Choose", buckets: ["suppliers", "decide"] },
  { id: "approve", label: "Approve", buckets: ["send", "po"] },
  { id: "waiting", label: "Waiting", buckets: ["waiting"] },
];
export const pipeOf = (b: Bucket): PipeId => PIPELINE.find((p) => p.buckets.includes(b))!.id;
export function pipelineCounts(g: Record<Bucket, readonly unknown[]>): Record<PipeId, number> {
  const out = { questions: 0, choose: 0, approve: 0, waiting: 0 } as Record<PipeId, number>;
  for (const p of PIPELINE) out[p.id] = p.buckets.reduce((n, b) => n + g[b].length, 0);
  return out;
}
