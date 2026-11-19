// Dev-only turn trace contract — SPEC.md v2.8.8, Appendix A.22 "Dev-only turn trace contract" (team decision 27).
// Served only by GET /dev/turns/{turnId}/trace outside production with DEV_TOOLS=1. Never sent to players.
// This file only validates shapes. It does no money or simulation math.
import { z } from "zod";
import { ConsumerReasonCode, CustomerArchetype, LedgerTag, MoneyCents, UUID } from "./shared.js";

export const TURN_TRACE_STEP_KEYS = [
  "player_actions_and_business_visitors", // Turn execution order step 1
  "month_end_bills_and_interest", // step 2
  "overdraft_fee", // step 3
  "negative_balance_interest", // step 4
  "fresh_start", // step 5
  "money_report", // step 6
] as const;
export const TurnTraceStepKey = z.enum(TURN_TRACE_STEP_KEYS);

/** Keys that must never appear in a trace (A.22: no agent identity, epsilon, relationship scores or account IDs). */
const FORBIDDEN_KEY = /^(consumer_?agent_?id|epsilon|relationship_?score|account_?id|user_?id)$/i;

export const TraceValue = z.union([z.string(), z.number(), z.boolean(), z.null()]);
const TraceValues = z
  .record(z.string(), TraceValue)
  .refine((r) => Object.keys(r).every((k) => !FORBIDDEN_KEY.test(k)), {
    message: "trace inputs/outputs must not contain agent IDs, epsilon, relationship scores or account IDs",
  });

export const TurnTraceLedgerPosting = z
  .object({
    tag: LedgerTag,
    amountCents: MoneyCents,
    balanceAfterCents: MoneyCents,
    businessId: UUID.nullable(),
  })
  .strict();

export const TurnTraceStep = z
  .object({
    stepNumber: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5), z.literal(6)]),
    stepKey: TurnTraceStepKey,
    skipped: z.boolean(),
    skipReason: z.string().min(1).nullable(),
    formulaIds: z.array(z.string().regex(/^F\d+$/, "formula IDs look like F12")),
    inputs: TraceValues,
    outputs: TraceValues,
    ledgerPostings: z.array(TurnTraceLedgerPosting),
  })
  .strict()
  .superRefine((step, ctx) => {
    if (TURN_TRACE_STEP_KEYS[step.stepNumber - 1] !== step.stepKey) {
      ctx.addIssue({ code: "custom", path: ["stepKey"], message: `step ${step.stepNumber} must be "${TURN_TRACE_STEP_KEYS[step.stepNumber - 1]}"` });
    }
    if (step.skipped && step.skipReason === null) {
      ctx.addIssue({ code: "custom", path: ["skipReason"], message: "a skipped step needs a skipReason" });
    }
    if (!step.skipped && step.skipReason !== null) {
      ctx.addIssue({ code: "custom", path: ["skipReason"], message: "only skipped steps have a skipReason" });
    }
    if (step.skipped && step.ledgerPostings.length > 0) {
      ctx.addIssue({ code: "custom", path: ["ledgerPostings"], message: "a skipped step posts nothing" });
    }
  });

/** NUMERIC(12,9) probability in [0, 1] as a decimal string. */
const Probability = z.string().regex(/^(0(\.\d{1,9})?|1(\.0{1,9})?)$/, "probability must be a decimal string in [0, 1] with at most 9 places");
/** NUMERIC(18,17) random draw in [0, 1) as a decimal string (A.14.1 rng01). */
const RandomDraw = z.string().regex(/^0(\.\d{1,17})?$/, "random draw must be a decimal string in [0, 1) with at most 17 places");

export const TurnTraceVisitor = z
  .object({
    visitorIndex: z.number().int().nonnegative(),
    archetype: CustomerArchetype,
    priceProbability: Probability,
    finalProbability: Probability,
    randomDraw: RandomDraw,
    reasonCode: ConsumerReasonCode,
    units: z.number().int().nonnegative(),
  })
  .strict();

export const TurnTraceResponse = z
  .object({
    turnId: UUID,
    turnNumber: z.number().int().positive(),
    simulationVersion: z.string().min(1),
    devOnly: z.literal(true),
    walletStartCents: MoneyCents,
    walletEndCents: MoneyCents,
    steps: z.array(TurnTraceStep).length(6),
    businesses: z.array(
      z
        .object({
          businessId: UUID,
          visitors: z.array(TurnTraceVisitor).superRefine((visitors, ctx) => {
            for (let i = 1; i < visitors.length; i++) {
              if (visitors[i].visitorIndex <= visitors[i - 1].visitorIndex) {
                ctx.addIssue({ code: "custom", path: [i, "visitorIndex"], message: "visitors must be sorted by unique visitorIndex" });
              }
            }
          }),
        })
        .strict(),
    ),
  })
  .strict()
  .superRefine((trace, ctx) => {
    trace.steps.forEach((step, i) => {
      if (step.stepNumber !== i + 1) {
        ctx.addIssue({ code: "custom", path: ["steps", i, "stepNumber"], message: "steps must be 1..6 in Turn execution order" });
      }
    });
  });

export type TurnTraceStepKey = z.infer<typeof TurnTraceStepKey>;
export type TraceValue = z.infer<typeof TraceValue>;
export type TurnTraceLedgerPosting = z.infer<typeof TurnTraceLedgerPosting>;
export type TurnTraceStep = z.infer<typeof TurnTraceStep>;
export type TurnTraceVisitor = z.infer<typeof TurnTraceVisitor>;
export type TurnTraceResponse = z.infer<typeof TurnTraceResponse>;
