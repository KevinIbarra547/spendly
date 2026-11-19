// Contract tests for the dev-only TurnTraceResponse (SPEC.md v2.8.8, A.22).
// MOCK DATA: the numbers below are made-up test values that only exercise the shape. They are not game results.
import { describe, expect, it } from "vitest";
import { TURN_TRACE_STEP_KEYS, TurnTraceResponse } from "../src/index.js";

const BIZ = "11111111-1111-4111-8111-111111111111";

function validTrace() {
  return {
    turnId: "22222222-2222-4222-8222-222222222222",
    turnNumber: 1,
    simulationVersion: "test-mock",
    devOnly: true as const,
    walletStartCents: 1000,
    walletEndCents: 1100,
    steps: TURN_TRACE_STEP_KEYS.map((stepKey, i) => ({
      stepNumber: (i + 1) as 1 | 2 | 3 | 4 | 5 | 6,
      stepKey,
      skipped: i !== 0,
      skipReason: i === 0 ? null : "MOCK: not triggered on this test turn",
      formulaIds: i === 0 ? ["F12", "F25"] : [],
      inputs: i === 0 ? { visitorsPerDay: 2, priceCents: 100 } : {},
      outputs: i === 0 ? { unitsSold: 1, grossRevenueCents: 100 } : {},
      ledgerPostings:
        i === 0 ? [{ tag: "business_receipts" as const, amountCents: 100, balanceAfterCents: 1100, businessId: BIZ }] : [],
    })),
    businesses: [
      {
        businessId: BIZ,
        visitors: [
          { visitorIndex: 0, archetype: "bargain_hunter" as const, priceProbability: "0.500000000", finalProbability: "0.500000000", randomDraw: "0.12345678901234567", reasonCode: "bought" as const, units: 1 },
          { visitorIndex: 1, archetype: "premium_buyer" as const, priceProbability: "0.400000000", finalProbability: "0.400000000", randomDraw: "0.9", reasonCode: "price_rejected" as const, units: 0 },
        ],
      },
    ],
  };
}

describe("TurnTraceResponse", () => {
  it("accepts a valid trace", () => {
    expect(TurnTraceResponse.safeParse(validTrace()).success).toBe(true);
  });

  it("rejects an agent ID on a visitor (players' anonymity rule)", () => {
    const t: any = validTrace();
    t.businesses[0].visitors[0].consumerAgentId = "33333333-3333-4333-8333-333333333333";
    expect(TurnTraceResponse.safeParse(t).success).toBe(false);
  });

  it("rejects epsilon or relationship scores hidden in step inputs/outputs", () => {
    const a: any = validTrace();
    a.steps[0].inputs.epsilon = 1.2;
    expect(TurnTraceResponse.safeParse(a).success).toBe(false);
    const b: any = validTrace();
    b.steps[0].outputs.relationship_score = "0.5";
    expect(TurnTraceResponse.safeParse(b).success).toBe(false);
  });

  it("rejects decimal or string cents", () => {
    const a: any = validTrace();
    a.walletEndCents = 11.5;
    expect(TurnTraceResponse.safeParse(a).success).toBe(false);
    const b: any = validTrace();
    b.steps[0].ledgerPostings[0].amountCents = "100";
    expect(TurnTraceResponse.safeParse(b).success).toBe(false);
  });

  it("rejects steps out of order, missing, or with the wrong key", () => {
    const swapped: any = validTrace();
    [swapped.steps[0], swapped.steps[1]] = [swapped.steps[1], swapped.steps[0]];
    expect(TurnTraceResponse.safeParse(swapped).success).toBe(false);
    const missing: any = validTrace();
    missing.steps.pop();
    expect(TurnTraceResponse.safeParse(missing).success).toBe(false);
    const wrongKey: any = validTrace();
    wrongKey.steps[2].stepKey = "fresh_start";
    expect(TurnTraceResponse.safeParse(wrongKey).success).toBe(false);
  });

  it("requires a reason for skipped steps and no postings on them", () => {
    const noReason: any = validTrace();
    noReason.steps[1].skipReason = null;
    expect(TurnTraceResponse.safeParse(noReason).success).toBe(false);
    const posted: any = validTrace();
    posted.steps[1].ledgerPostings = [{ tag: "rent_utilities", amountCents: -100, balanceAfterCents: 1000, businessId: null }];
    expect(TurnTraceResponse.safeParse(posted).success).toBe(false);
  });

  it("rejects visitors out of visitorIndex order and bad decimal strings", () => {
    const unsorted: any = validTrace();
    unsorted.businesses[0].visitors.reverse();
    expect(TurnTraceResponse.safeParse(unsorted).success).toBe(false);
    const badProb: any = validTrace();
    badProb.businesses[0].visitors[0].finalProbability = "1.2";
    expect(TurnTraceResponse.safeParse(badProb).success).toBe(false);
    const badDraw: any = validTrace();
    badDraw.businesses[0].visitors[0].randomDraw = 0.5;
    expect(TurnTraceResponse.safeParse(badDraw).success).toBe(false);
  });

  it("requires devOnly: true", () => {
    const t: any = validTrace();
    t.devOnly = false;
    expect(TurnTraceResponse.safeParse(t).success).toBe(false);
  });
});
