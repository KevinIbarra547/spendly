"""Spendly engine formula reference, SPEC.md v2.8.6 (Section 4 F1-F27, Appendix A.26 M1-M16).

STANDALONE SPECIFICATION FIXTURE -- NOT THE SPENDLY APPLICATION ENGINE.
Every formula is owned by its listed owner (almost all by Ethan). This file only
restates the frozen spec as runnable code and checks it against the spec's own
worked examples and edge cases. It sets no new game values. If this file and
SPEC.md disagree, SPEC.md wins and this file is the bug.

Run:  python3 -I tests/fixtures/engine_formulas_reference.py
Uses only the Python standard library. No network, no user data.

Conventions (SPEC Section 4.A and v1.1 D2):
- Money is integer cents. Percentage math uses Decimal; a ledger amount is
  rounded once, when posted, half away from zero (`round_half_away_to_cent`).
- Probabilities use floats, matching the existing consumer_agents_reference.py
  oracle (Appendix A.26 Section 11).
- Random draws use the canonical A.14.1 `rng01`.
"""
from __future__ import annotations

import hashlib
import importlib.util
import math
from dataclasses import dataclass, field
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

D = Decimal

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def round_half_away_to_cent(value) -> int:
    """D2 rounding: Decimal input in cents, half away from zero, to whole cents.

    Python's Decimal ROUND_HALF_UP rounds ties away from zero for negatives too.
    Floats are converted through str() so binary float error never decides a tie.
    """
    if isinstance(value, float):
        value = D(str(value))
    return int(D(value).quantize(D("1"), rounding=ROUND_HALF_UP))


def clamp(value, low, high):
    return max(low, min(high, value))


def rng01(parts: list[object]) -> float:
    """A.14.1: SHA-256 of '|'.join(parts); bytes 0-7 big-endian, >> 11, / 2^53."""
    joined = "|".join(map(str, parts))
    if any("|" in str(p) for p in parts):
        raise ValueError("RNG key component may not contain '|'")
    digest = hashlib.sha256(joined.encode("utf-8")).digest()
    return (int.from_bytes(digest[:8], "big") >> 11) / (2**53)


def seeded_index(u: float, n: int) -> int:
    """A.14.1 selection rule: min(floor(u*n), n-1)."""
    if n <= 0:
        raise ValueError("cannot select from an empty candidate list")
    return min(int(math.floor(u * n)), n - 1)


# ---------------------------------------------------------------------------
# Constants (SPEC Section 4.A notation table and Appendix A)
# ---------------------------------------------------------------------------
MONTH_TURNS = 30
WEEK_TURNS = 7
TAX_RATE = D("0.07")
FEE_OVERDRAFT_CENTS = 500
NEG_BALANCE_ANNUAL_RATE = D("0.12")
FRESH_START_THRESHOLD_CENTS = -20000
FRESH_START_LIMIT = {"free": 3, "premium": 5}
P_EVENT = 0.10
TIER_COMMON_BELOW, TIER_UNCOMMON_BELOW = 0.60, 0.90
EVENT_CARDS = {  # Appendix A.4 card IDs
    "Common": ["social-buzz", "good-weather", "supplier-discount", "quiet-day",
               "rate-hike-cut", "inflation-report", "earnings-beat-miss"],
    "Uncommon": ["competitor-promotion", "equipment-issue", "sector-boom", "product-recall"],
    "Rare": ["community-festival", "market-dip-crash"],
}
BASE_CUSTOMER_MAX_CENTS = {"bargain": 100, "loyal": 240, "premium": 400}
LOYALTY_MULTIPLIER = {"bargain": 1.00, "loyal": 1.10, "premium": 1.00}
COGS_RATIO = {"make": D("0.30"), "resell": D("0.65"), "service": D("0"), "big_build": D("0.35")}
PLATFORM_FEE_RATE = D("0.08")
PHYSICAL_MONTHLY_BILL_CENTS = 1800
EMPLOYEE_COST_CENTS = 0
SUPPLIER_DISCOUNT_FACTOR = D("0.90")
CPI_MONTHLY_CLAMP = D("0.02")
AI_CAP_DAILY = {"free": 10, "premium": 30}
AI_MONTHLY_BUDGET_DOLLARS = D("20.00")
AI_RESERVED_OUTPUT_TOKENS = 750
LESSON_REWARD_POINTS = 10
PREMIUM_DISPLAY_PRICE_CENTS = 1000
PREMIUM_ACTUAL_CHARGE_MVP_CENTS = 0
STARTING_CASH_CENTS = 10000
PAPER_ACCOUNT_START_CENTS = 100000
LOANS = {  # Appendix A.3 baselines
    "personal": {"principal_cents": 5000, "apr": D("0.12"), "term_months": 6},
    "business": {"principal_cents": 10000, "apr": D("0.08"), "term_months": 6},
}
SAVINGS_APR = {"basic": D("0.01"), "locked": D("0.03")}
LOCKED_SAVINGS_TURNS = 90
POOL = {"bargain": range(0, 40), "loyal": range(40, 80), "premium": range(80, 100)}
EPSILON_DEFAULT, EPSILON_MIN, EPSILON_MAX = 1.20, 0.30, 3.00
RELATIONSHIP_INITIAL = 0.50

# ===========================================================================
# Wallet and debt
# ===========================================================================


def f1_wallet_next(wallet_cents: int, credits: list[int], debits: list[int]) -> int:
    """F1: W_(t+1) = W_t + SUM(credits) - SUM(debits). Amounts are positive cents."""
    return wallet_cents + sum(credits) - sum(debits)


def week_of(turn: int) -> int:
    """F2: seven-turn week bucket. Turns 1-7 -> 1, 8-14 -> 2, ..."""
    if turn < 1:
        raise ValueError("turns start at 1")
    return (turn - 1) // WEEK_TURNS + 1


def f2_debit_crosses_zero(balance_before: int, balance_after: int) -> bool:
    """F2: set the pending crossing flag only on a nonnegative -> negative move."""
    return balance_before >= 0 and balance_after < 0


def f2_overdraft_fee_stage(pending_crossing: bool, last_fee_week: int | None,
                           effective_turn: int) -> tuple[int, int | None]:
    """F2 fee stage. Returns (fee_cents, new_last_fee_week). Caller clears the flag after."""
    week = week_of(effective_turn)
    if pending_crossing and last_fee_week != week:
        return FEE_OVERDRAFT_CENTS, week
    return 0, last_fee_week


def f3_negative_balance_interest(end_of_turn_cents: int, turn: int) -> int:
    """F3: on turns 7, 14, 21...: round(|negative balance| x 0.12 / 52). Returns a debit."""
    if turn % WEEK_TURNS != 0 or end_of_turn_cents >= 0:
        return 0
    return round_half_away_to_cent(D(abs(end_of_turn_cents)) * NEG_BALANCE_ANNUAL_RATE / 52)


def f4_fresh_start(end_of_turn_cents: int, uses_consumed: int,
                   entitlement_limit: int) -> tuple[int, int, int]:
    """F4: returns (credit_cents, final_wallet_cents, uses_consumed_after)."""
    if end_of_turn_cents <= FRESH_START_THRESHOLD_CENTS and uses_consumed < entitlement_limit:
        credit = 0 - end_of_turn_cents
        return credit, 0, uses_consumed + 1
    return 0, end_of_turn_cents, uses_consumed


# ===========================================================================
# Events
# ===========================================================================


def f5_tier_from_roll(tier_roll: float) -> str:
    if tier_roll < TIER_COMMON_BELOW:
        return "Common"
    if tier_roll < TIER_UNCOMMON_BELOW:
        return "Uncommon"
    return "Rare"


def f5_draw_event(simulation_version: str, account_id: str, turn: int,
                  used_cards: dict[str, set[str]]) -> str | None:
    """F5 + A.14.1: returns the drawn card ID (and marks it used) or None.

    A tier resets only after every card in it has fired once.
    """
    if rng01([simulation_version, account_id, turn, "event-trigger"]) >= P_EVENT:
        return None
    tier = f5_tier_from_roll(rng01([simulation_version, account_id, turn, "event-tier"]))
    used = used_cards.setdefault(tier, set())
    if len(used) == len(EVENT_CARDS[tier]):
        used.clear()
    unused = sorted(c for c in EVENT_CARDS[tier] if c not in used)
    u = rng01([simulation_version, account_id, turn, tier, "event-card"])
    card = unused[seeded_index(u, len(unused))]
    used.add(card)
    return card


# ===========================================================================
# Business sales
# ===========================================================================


def f6_f14_sales_tax(taxable_gross_sales_cents: int) -> int:
    """F6/F14: one sales_tax entry per business per turn = round(gross x 0.07)."""
    return round_half_away_to_cent(D(taxable_gross_sales_cents) * TAX_RATE)


def f7_customer_max_price_cents(customer_type: str, business_price_scale) -> int:
    return round_half_away_to_cent(D(BASE_CUSTOMER_MAX_CENTS[customer_type]) * D(str(business_price_scale)))


def f7_buy_probability(selling_price_cents: int, customer_max_price_cents: int,
                       customer_type: str) -> float:
    """F7: clamp(0, 1, (1 - (price/max)^2) x loyalty)."""
    if customer_max_price_cents <= 0:
        raise ValueError("customer max price must be positive (catalog/config error)")
    base = 1 - (selling_price_cents / customer_max_price_cents) ** 2
    return clamp(base * LOYALTY_MULTIPLIER[customer_type], 0.0, 1.0)


def f12_units_sold(purchase_intents: list[bool], capacity: int) -> int:
    """F12: demand = count of intents; units/jobs sold = min(demand, stock or jobs left)."""
    return min(sum(1 for x in purchase_intents if x), max(0, capacity))


def f13_gross_revenue(selling_price_cents: int, units_by_customer_type: dict[str, int]) -> int:
    """F13: SUM(price x units sold to each customer type)."""
    return sum(selling_price_cents * units for units in units_by_customer_type.values())


def f15_base_unit_cost_cents(default_price_cents: int, base_type: str) -> int:
    return round_half_away_to_cent(D(default_price_cents) * COGS_RATIO[base_type])


def f15_bulk_discount(units_ordered: int) -> Decimal:
    """A.2: 0 below 25 units; 5% for 25-99; 10% for 100+ (max 1,000 per order)."""
    if units_ordered > 1000:
        raise ValueError("maximum 1,000 units per order")
    if units_ordered >= 100:
        return D("0.10")
    if units_ordered >= 25:
        return D("0.05")
    return D("0")


def f15_restock_cash_debit(units_ordered: int, current_unit_cost_cents: int,
                           supplier_discount_active: bool) -> int:
    """F15: subtotal x (1 - bulk) x supplier factor, multiplicative, rounded once."""
    subtotal = D(units_ordered * current_unit_cost_cents)
    factor = SUPPLIER_DISCOUNT_FACTOR if supplier_discount_active else D("1")
    return round_half_away_to_cent(subtotal * (1 - f15_bulk_discount(units_ordered)) * factor)


def f15_inflation_adjusted_unit_cost(previous_month_unit_cost_cents: int,
                                     monthly_cpi_change) -> int:
    """F15/A.2: apply only a newly observed CPI change, clamped to +/-2%, rounded each month."""
    change = clamp(D(str(monthly_cpi_change)), -CPI_MONTHLY_CLAMP, CPI_MONTHLY_CLAMP)
    return round_half_away_to_cent(D(previous_month_unit_cost_cents) * (1 + change))


def f15_fifo_cogs(lots: list[list[int]], units_sold: int) -> int:
    """F15: consume oldest lots first. lots = [[units_remaining, unit_cost_cents], ...] (mutated)."""
    cogs, remaining = 0, units_sold
    for lot in lots:
        if remaining == 0:
            break
        take = min(lot[0], remaining)
        cogs += take * lot[1]
        lot[0] -= take
        remaining -= take
    if remaining:
        raise ValueError("sold more units than inventory holds")
    return cogs


def f15_online_platform_fee(gross_online_sales_cents: int) -> int:
    return round_half_away_to_cent(D(gross_online_sales_cents) * PLATFORM_FEE_RATE)


def f15_physical_monthly_bill(turn: int, is_physical: bool) -> int:
    return PHYSICAL_MONTHLY_BILL_CENTS if is_physical and turn % MONTH_TURNS == 0 else 0


def f15_business_contribution(gross_sales: int, sales_tax: int, cogs: int,
                              platform_fee: int, physical_bill: int,
                              employee_cost: int = EMPLOYEE_COST_CENTS) -> int:
    """F15/F20: gross - tax - COGS - platform fee - rent/utilities - employees."""
    return gross_sales - sales_tax - cogs - platform_fee - physical_bill - employee_cost


def f16_break_even_units(price_cents: int, variable_cost_cents: int,
                         sales_tax_per_unit_cents: int, fixed_costs_cents: int) -> int | None:
    """F16 (STRETCH, not approved for MVP): None means no finite break-even."""
    unit_contribution = price_cents - variable_cost_cents - sales_tax_per_unit_cents
    if unit_contribution <= 0:
        return None
    return math.ceil(Fraction(fixed_costs_cents, unit_contribution))


# ===========================================================================
# Stocks (paper trading is a separate account; the wallet never changes)
# ===========================================================================


def f9_holding_value_cents(shares_micros: int, price_micros: int) -> Fraction:
    """F9: shares x price, exact, in cents (micro-shares x micro-dollars / 1e10)."""
    return Fraction(shares_micros * price_micros, 10_000_000_000)


def f10_trade(side: str, shares_micros: int, execution_price_micros: int,
              paper_cash_cents: int, wallet_cents: int) -> tuple[int, int, int]:
    """F10: returns (cash_change_cents, paper_cash_after, wallet_after).

    Buys round up, sells round down, notional below 1 cent is rejected.
    """
    if shares_micros <= 0:
        raise ValueError("TRADE_ZERO_SHARES")
    notional = f9_holding_value_cents(shares_micros, execution_price_micros)
    if notional < 1:
        raise ValueError("TRADE_NOTIONAL_BELOW_MINIMUM")
    if side == "buy":
        cost = math.ceil(notional)
        if cost > paper_cash_cents:
            raise ValueError("INSUFFICIENT_PRACTICE_CASH")
        return -cost, paper_cash_cents - cost, wallet_cents
    if side == "sell":
        proceeds = math.floor(notional)
        return proceeds, paper_cash_cents + proceeds, wallet_cents
    raise ValueError("side must be buy or sell")


def f17_paper_portfolio_value(paper_cash_cents: int,
                              holdings: list[tuple[int, int]]) -> Fraction:
    """F17: paper cash + SUM(holding values). Never added to the wallet."""
    return paper_cash_cents + sum((f9_holding_value_cents(s, p) for s, p in holdings), Fraction(0))


# ===========================================================================
# Learn, Coach and Premium
# ===========================================================================


def f8_required_correct(question_count: int) -> int:
    """F8: ceil(0.70 x n), computed in integers.

    (7n + 9) // 10 is the exact integer ceiling, so no float rounding can ever
    disagree with the spec's authoritative table (4->3 ... 10->7).
    """
    return (7 * question_count + 9) // 10


def f8_quiz_passed(correct_answers: int, question_count: int) -> bool:
    return correct_answers >= f8_required_correct(question_count)


def f11_coach_question_allowed(questions_used_today: int, plan: str) -> bool:
    return questions_used_today < AI_CAP_DAILY[plan]


def f18_lesson_reward(quiz_passed: bool, already_granted: bool) -> int:
    """F18: 10 points on the first pass only. Never wallet cash."""
    return LESSON_REWARD_POINTS if quiz_passed and not already_granted else 0


def f19_coach_call_allowed(estimated_input_tokens: int, input_rate_per_million,
                           output_rate_per_million, month_actual_cost,
                           month_pending_reservations, daily_cap_allows: bool,
                           pricing_config_is_current: bool) -> tuple[bool, Decimal]:
    """F19: returns (allowed, estimated_cost_dollars). Shared $20/month across providers."""
    estimate = (D(estimated_input_tokens) * D(str(input_rate_per_million)) / 1_000_000
                + D(AI_RESERVED_OUTPUT_TOKENS) * D(str(output_rate_per_million)) / 1_000_000)
    available = AI_MONTHLY_BUDGET_DOLLARS - D(str(month_actual_cost)) - D(str(month_pending_reservations))
    allowed = daily_cap_allows and pricing_config_is_current and estimate <= available
    return allowed, estimate


def f21_premium_checkout() -> dict:
    """F21: $10/month displayed, $0 charged, mock entitlement only."""
    return {"display_price_cents": PREMIUM_DISPLAY_PRICE_CENTS,
            "charged_cents": PREMIUM_ACTUAL_CHARGE_MVP_CENTS,
            "payment_processor_called": False}


def f22_starting_cash(lesson_0_completed: bool, already_posted: bool) -> int:
    """F22: +$100 (tag starting_cash) exactly once per account."""
    return STARTING_CASH_CENTS if lesson_0_completed and not already_posted else 0


# ===========================================================================
# Money Report
# ===========================================================================
EXPENSE_TIE_ORDER = ["inventory_purchase", "rent_utilities", "platform_fee", "sales_tax",
                     "loan_interest", "debt_interest", "overdraft_fee"]


def f20_money_report(opening_wallet: int, closing_wallet: int,
                     ledger: list[tuple[str, int]],
                     contributions: dict[str, tuple[int, str, str]]) -> dict:
    """F20/A.5. ledger = [(tag, signed_cents)]. contributions = {business_id:
    (contribution_cents, catalog_id, created_at_iso)}.
    """
    net = closing_wallet - opening_wallet
    if net != sum(amount for _tag, amount in ledger):
        raise ValueError("report does not reconcile to wallet ledger")
    spent = {}
    for tag, amount in ledger:
        if amount < 0:
            spent[tag] = spent.get(tag, 0) + -amount
    cost_of_debt = sum(spent.get(t, 0) for t in ("loan_interest", "debt_interest", "overdraft_fee"))
    expenses = [(spent[t], -EXPENSE_TIE_ORDER.index(t), t) for t in EXPENSE_TIE_ORDER if spent.get(t)]
    biggest_drain = max(expenses)[2] if expenses else None
    top_earner = None
    if contributions:
        top_earner = sorted(contributions.items(),
                            key=lambda kv: (-kv[1][0], kv[1][1], kv[1][2]))[0][0]
    return {"wallet_net_change": net, "cost_of_debt": cost_of_debt,
            "biggest_drain": biggest_drain, "top_earner": top_earner}


# ===========================================================================
# Loans and savings
# ===========================================================================


def f23_scheduled_payment(principal_cents: int, apr: Decimal, term_months: int) -> int:
    r = apr / 12
    return round_half_away_to_cent(D(principal_cents) * r / (1 - (1 + r) ** -term_months))


def f23_amortization(principal_cents: int, apr: Decimal, term_months: int) -> list[dict]:
    """F23: each row splits the installment into loan_interest + loan_principal.
    The final installment is opening principal + interest so principal ends at exactly 0.
    """
    r = apr / 12
    payment = f23_scheduled_payment(principal_cents, apr, term_months)
    rows, opening = [], principal_cents
    for month in range(1, term_months + 1):
        interest = round_half_away_to_cent(D(opening) * r)
        installment = opening + interest if month == term_months else payment
        principal_part = installment - interest
        rows.append({"month": month, "turn": month * MONTH_TURNS, "opening": opening,
                     "interest": interest, "principal": principal_part,
                     "installment": installment, "closing": opening - principal_part})
        opening -= principal_part
    return rows


def f23_early_payoff(remaining_principal_cents: int, apr: Decimal, elapsed_turns: int) -> int:
    """F23: principal + round(principal x APR x elapsed_turns / 360)."""
    return remaining_principal_cents + round_half_away_to_cent(
        D(remaining_principal_cents) * apr * elapsed_turns / 360)


def f24_monthly_interest(balance_at_period_start_cents: int, jar_type: str) -> int:
    """F24: round(start-of-period balance x APR / 12), credited inside the jar."""
    return round_half_away_to_cent(D(balance_at_period_start_cents) * SAVINGS_APR[jar_type] / 12)


@dataclass
class LockedLot:
    deposit_turn: int
    principal: int
    interest: int = 0

    @property
    def maturity_turn(self) -> int:
        return self.deposit_turn + LOCKED_SAVINGS_TURNS


def f24_locked_withdraw(lots: list[LockedLot], requested_cents: int, turn: int) -> int:
    """F24: only matured lots, FIFO, principal then interest within each lot (mutates lots)."""
    matured = [lot for lot in lots if turn >= lot.maturity_turn]
    if requested_cents > sum(lot.principal + lot.interest for lot in matured):
        raise ValueError("LOCKED_SAVINGS_NOT_MATURED")
    remaining = requested_cents
    for lot in matured:
        for part in ("principal", "interest"):
            take = min(getattr(lot, part), remaining)
            setattr(lot, part, getattr(lot, part) - take)
            remaining -= take
    return requested_cents


# ===========================================================================
# Shopper model (F25-F27; M2 and M4 are the same MVP rules)
# ===========================================================================


def f25_assign_visitors_for_turn(simulation_version: str, account_id: str, turn: int,
                                 businesses: list[tuple[str, int]]) -> list[tuple[str, int, int, str]]:
    """F12/F25 + A.14.1: one shared 100-agent pool per turn, businesses by UUID ascending.

    businesses = [(business_uuid, visitors_per_day)].
    Returns [(business_id, visitor_index, agent_index, customer_type)].
    """
    available = set(range(100))
    out = []
    for business_id, visitors in sorted(businesses, key=lambda b: b[0]):
        for vi in range(visitors):
            key = [simulation_version, account_id, business_id, turn, vi]
            u_type = rng01(key + ["customer-type"])
            ctype = "bargain" if u_type < 0.40 else "loyal" if u_type < 0.80 else "premium"
            candidates = sorted(i for i in available if i in POOL[ctype])
            if not candidates:
                raise RuntimeError("archetype pool exhausted; abort turn atomically")
            agent = candidates[seeded_index(rng01(key + ["consumer-agent-assignment"]), len(candidates))]
            available.remove(agent)
            out.append((business_id, vi, agent, ctype))
    return out


def f26_purchase_probability(price_cents: int, max_price_cents: int, customer_type: str,
                             epsilon: float, relationship: float) -> dict:
    """F26/M2. Returns every intermediate so F27 can reuse it."""
    if max_price_cents <= 0:
        raise ValueError("p_max <= 0: catalog/configuration error, fail the turn")
    epsilon = clamp(epsilon, EPSILON_MIN, EPSILON_MAX)
    p_source = clamp(1 - (price_cents / max_price_cents) ** 2, 0.0, 1.0)
    p_price = p_source ** (epsilon / 1.20) if p_source > 0 else 0.0
    m_type = LOYALTY_MULTIPLIER[customer_type]
    m_rel = 0.90 + 0.20 * relationship
    p_buy_raw = p_price * m_type * m_rel
    return {"p_source": p_source, "p_price": p_price, "m_type": m_type, "m_rel": m_rel,
            "p_buy_raw": p_buy_raw, "p_buy": clamp(p_buy_raw, 0.0, 1.0)}


def f27_relationship_next(relationship: float, experience_signal: int) -> float:
    """F27/M4: +1 fulfilled, -1 wanted but out of stock/capacity, 0 normal rejection."""
    return clamp(relationship + 0.02 * experience_signal, 0.0, 1.0)


def f27_epsilon_gradient(prob: dict, epsilon: float) -> float:
    if 0 < prob["p_source"] < 1 and 0 < prob["p_buy_raw"] < 1:
        return prob["m_type"] * prob["m_rel"] * (prob["p_price"] / 1.20) * math.log(prob["p_source"])
    return 0.0


def f27_epsilon_next(prob: dict, epsilon: float, observed_buy: int) -> float:
    """F27/M4: gradient step on P_buy, step-limited to +/-5%, clamped to [0.30, 3.00].
    Do not call for closures, event suppression, or stockout after intent.
    """
    raw = epsilon - 0.05 * (prob["p_buy"] - observed_buy) * f27_epsilon_gradient(prob, epsilon)
    step_limited = clamp(raw, epsilon * 0.95, epsilon * 1.05)
    return clamp(step_limited, EPSILON_MIN, EPSILON_MAX)


# ===========================================================================
# Resident model, Appendix A.26 (M1, M3, M5-M16 are STRETCH)
# ===========================================================================


def m1_product_score(price_cents: int, budget_cents: int, quality: float,
                     quality_weight: float, theta: float = 0.35):
    """M1: S = wq*q + (1-wq)*(1-p/B). Returns 'over_budget' or (score, acceptable)."""
    if budget_cents <= 0 or price_cents > budget_cents:
        return "over_budget"
    s = quality_weight * quality + (1 - quality_weight) * (1 - price_cents / budget_cents)
    return s, s >= theta


def m3_business_probabilities(weights: dict[str, float], last_happy: str | None = None,
                              return_prob: float = 0.25):
    """M3: P(b) = w_b / sum(w), mixed with lambda for the last-happy business."""
    total = sum(weights.values())
    if total == 0:
        return "no_eligible_business"
    probs = {b: w / total for b, w in weights.items()}
    if last_happy in weights:
        probs = {b: (1 - return_prob) * p for b, p in probs.items()}
        probs[last_happy] += return_prob
    return probs


def m5_spawn_probability(population: int, funds_cents: int, cap: int = 500) -> float:
    if population >= cap:
        return 0.0
    return 0.001 * min(1, max(0, funds_cents) / 10000)


def m5_child_trait(parent_trait: float, z: float, lower: float, upper: float) -> float:
    return clamp(parent_trait * (1 + clamp(z, -0.10, 0.10)), lower, upper)


def m5_child_transfer(parent_funds_cents: int) -> int:
    return min(parent_funds_cents, round_half_away_to_cent(D(parent_funds_cents) * D("0.05")))


def m6_daily_budget(opening_funds_cents: int, income_today_cents: int) -> int:
    available = max(0, opening_funds_cents + income_today_cents)
    return int(min(D(available), max(D(0), D("0.20") * opening_funds_cents + income_today_cents))
               .to_integral_value(rounding=ROUND_FLOOR))


def m7_needs(h, t, s, hours_awake, hours_slept, ate, drank, home_quality):
    if hours_awake + hours_slept > 24:
        raise ValueError("invalid schedule: more than 24 hours")
    return (clamp(min(1, h + 0.04 * hours_awake) - 0.55 * ate, 0, 1),
            clamp(min(1, t + 0.06 * hours_awake) - 0.65 * drank, 0, 1),
            clamp(min(1, s + 0.05 * hours_awake) - 0.15 * hours_slept * home_quality, 0, 1))


def m7_urgency(need: float, trigger: float) -> float:
    if trigger >= 1:
        raise ValueError("trigger must be < 1")
    return clamp((need - trigger) / (1 - trigger), 0, 1)


def m8_mood(drivers: list[float], weights: list[float], prior_mood: float,
            loyalty: float, epsilon: float) -> dict:
    if abs(sum(weights) - 1) > 1e-9:
        raise ValueError("mood weights must sum to 1")
    target = sum(a * x for a, x in zip(weights, drivers))
    mood = clamp(prior_mood + 0.05 * (target - prior_mood), 0, 1)
    return {"target": target, "mood": mood,
            "lambda_eff": clamp(loyalty * (0.8 + 0.4 * mood), 0, 0.90),
            "epsilon_eff": clamp(epsilon * (1.2 - 0.4 * mood), 0.30, 3.00)}


def m9_departure(age_days: float, delta_days: float = 1, h0=0.001, k=0.002, a0=1800):
    if age_days < 0 or delta_days < 0:
        raise ValueError("negative age or delta")
    hazard = min(20, h0 * math.exp(k * (age_days - a0)))
    return hazard, 1 - math.exp(-hazard * delta_days)


def m10_move_probability(rent_cents: int, income_cents: int, days_over: int) -> float:
    if income_cents > 0:
        a = rent_cents / income_cents
    else:
        a = math.inf if rent_cents > 0 else 0.0
    if a > 0.50 and days_over >= 7:
        return clamp(0.05 + 0.50 * max(0, a - 0.50), 0.05, 0.50)
    return 0.0


def m11_walk_away(m0, pressure, strength, wage_min, wage_max) -> float:
    if wage_min <= 0 or wage_max < wage_min:
        raise ValueError("invalid job posting")
    return clamp(m0 * (1 - 0.20 * pressure + 0.15 * strength), wage_min, wage_max)


def m11_accept_probability(offer, minimum) -> float:
    if minimum <= 0:
        raise ValueError("invalid minimum")
    if offer >= minimum:
        return 1.0
    if offer >= 0.90 * minimum:
        return 1 - (minimum - offer) / (0.10 * minimum)
    return 0.0


def m12_age_profile(age_days: int, epsilon: float = EPSILON_DEFAULT) -> dict:
    if not 0 <= age_days <= 3650:
        raise ValueError("age out of range")
    a = clamp(age_days / 3650, 0, 1)
    return {"initial_funds": round_half_away_to_cent(D(10000) * (D("0.75") + D("0.50") * D(str(a)))),
            "epsilon_age": clamp(epsilon * (1.20 - 0.40 * a), 0.30, 3.00),
            "lambda_age": clamp(0.25 * (0.75 + 0.50 * a), 0, 0.90),
            "daily_share": 0.20 - 0.10 * a}


def m13_food_multiplier(hour: int) -> float:
    if not 0 <= hour <= 23:
        raise ValueError("hour out of range")
    return 1.15 if 7 <= hour < 10 else 1.25 if 11 <= hour < 15 else 1.20 if 17 <= hour < 21 else 1.00


def m13_drink_multiplier(hour: int, good_weather: bool = False) -> float:
    if not 0 <= hour <= 23:
        raise ValueError("hour out of range")
    return (1.15 if 10 <= hour < 20 else 1.00) * (1.10 if good_weather else 1.00)


def m13_craving(interest: float, epsilon: float) -> tuple[float, float]:
    return interest * 1.20, clamp(epsilon * 0.95, 0.30, 3.00)


def m14_job_score(wage_fit, hours_fit, skill_fit) -> float:
    return 0.40 * wage_fit + 0.30 * hours_fit + 0.30 * skill_fit


def m14_reliability(sleep_need, hunger, thirst, health, mood) -> float:
    return clamp(1 - 0.20 * sleep_need - 0.15 * hunger - 0.20 * thirst
                 - 0.15 * (1 - health) + 0.10 * (mood - 0.50), 0, 1)


def m14_effective_skill(base_skill, age_norm, reliability) -> float:
    return clamp(base_skill * (0.90 + 0.20 * age_norm) * reliability, 0, 1)


def m14_job_morale(wage_satisfaction, hours_fit, mood) -> float:
    return 0.40 * wage_satisfaction + 0.30 * hours_fit + 0.30 * mood


def m14_weekly_pay(hourly_wage_cents: int, hours) -> int:
    if hours > 60:
        raise ValueError("hours over 60 are rejected")
    h = D(str(hours))
    return round_half_away_to_cent(D(hourly_wage_cents) * (min(h, D(40)) + D("1.5") * max(D(0), h - 40)))


def m15_deprivation_days(days: int, funds_cents: int, hunger, thirst, health) -> int:
    deprived = funds_cents == 0 or hunger >= 0.95 or thirst >= 0.95 or health <= 0.10
    return days + 1 if deprived else 0


def m15_departure_transfer(resident_funds_cents: int) -> tuple[int, int]:
    amount = max(0, resident_funds_cents)
    return -amount, amount  # resident debit, CITY_RESERVE credit


def m16_injury(health: float) -> float:
    return clamp(health - 0.10, 0, 1)


def m16_rest(health: float) -> float:
    return clamp(health + 0.20, 0, 1)


# ===========================================================================
# Self-checks: the spec's own worked examples and edge cases
# ===========================================================================


@dataclass
class Checks:
    results: list[tuple[str, str]] = field(default_factory=list)

    def check(self, name: str, fn) -> None:
        try:
            fn()
            self.results.append((name, "PASS"))
        except Exception as exc:  # noqa: BLE001 - report every failure, keep going
            self.results.append((name, f"FAIL: {type(exc).__name__}: {exc}"))


def near(a, b, tol=1e-6) -> None:
    assert abs(float(a) - float(b)) <= tol, f"{a} != {b}"


def raises(fn, *args) -> None:
    try:
        fn(*args)
    except (ValueError, RuntimeError):
        return
    raise AssertionError(f"{fn.__name__}{args} did not raise")


def load_consumer_fixture():
    path = Path(__file__).with_name("consumer_agents_reference.py")
    spec = importlib.util.spec_from_file_location("consumer_agents_reference", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_checks() -> list[tuple[str, str]]:
    c = Checks()

    def rounding():
        assert round_half_away_to_cent(D("2.5")) == 3
        assert round_half_away_to_cent(D("-2.5")) == -3
        assert round_half_away_to_cent(D("2.4999")) == 2
        assert round_half_away_to_cent(0.125 * 100) == 13
    c.check("D2 rounding: half away from zero, including negatives", rounding)

    c.check("F1 wallet: 10,000c - 250c debit = 9,750c",
            lambda: (assert_eq(f1_wallet_next(10000, [], [250]), 9750)))

    def f2():
        assert f2_debit_crosses_zero(100, -1)
        assert not f2_debit_crosses_zero(100, 0)      # exactly $0 does not cross
        assert not f2_debit_crosses_zero(-5, -10)     # already negative
        assert [week_of(t) for t in (1, 7, 8, 14, 15)] == [1, 1, 2, 2, 3]
        fee, last = f2_overdraft_fee_stage(True, None, 3)
        assert (fee, last) == (500, 1)
        assert f2_overdraft_fee_stage(True, last, 6) == (0, 1)   # weekly cap
        assert f2_overdraft_fee_stage(True, last, 8) == (500, 2)
        assert f2_overdraft_fee_stage(False, None, 8) == (0, None)
    c.check("F2 overdraft: $5 once per 7-turn week; $0 does not cross", f2)

    def f3():
        assert f3_negative_balance_interest(-10000, 7) == 23    # spec test: -$100 -> $0.23
        assert f3_negative_balance_interest(-10000, 6) == 0
        assert f3_negative_balance_interest(0, 14) == 0
        assert f3_negative_balance_interest(500, 14) == 0
    c.check("F3 negative interest: -$100 at turn 7 -> 23c; only turns 7,14,...", f3)

    def f4():
        assert f4_fresh_start(-20300, 0, 3) == (20300, 0, 1)    # spec example -$203
        assert f4_fresh_start(-20000, 2, 3) == (20000, 0, 3)    # exactly -$200 triggers
        assert f4_fresh_start(-19999, 0, 3) == (0, -19999, 0)
        assert f4_fresh_start(-25000, 3, 3) == (0, -25000, 3)   # no uses left
        assert f4_fresh_start(-25000, 3, FRESH_START_LIMIT["premium"]) == (25000, 0, 4)
    c.check("F4 Fresh Start: <= -$200 resets to $0 while uses remain (3 free, 5 premium)", f4)

    def f5():
        assert f5_tier_from_roll(0.72) == "Uncommon"            # spec example
        assert [f5_tier_from_roll(x) for x in (0.0, 0.5999, 0.60, 0.8999, 0.90)] == \
            ["Common", "Common", "Uncommon", "Uncommon", "Rare"]
        assert sum(map(len, EVENT_CARDS.values())) == 13
        used, fired = {}, []
        for turn in range(1, 2000):
            card = f5_draw_event("2.8.3", "acct", turn, used)
            if card:
                fired.append((turn, card))
        assert fired, "no events fired in 2,000 turns"
        replay = {}
        assert [(t, f5_draw_event("2.8.3", "acct", t, replay)) for t, _ in fired] == fired
        rare = [card for _, card in fired if card in EVENT_CARDS["Rare"]]
        for i in range(0, len(rare) - 1, 2):                    # no repeat inside a cycle
            assert rare[i] != rare[i + 1]
        rate = len(fired) / 1999
        assert 0.07 < rate < 0.13, rate
    c.check("F5 events: 10% trigger, 60/30/10 tiers, no repeat until tier exhausted, replayable", f5)

    def f6():
        assert f6_f14_sales_tax(0) == 0
        assert f6_f14_sales_tax(12800) == 896                   # $128 -> $8.96
        assert f6_f14_sales_tax(150) == 11                      # 10.5c rounds up
    c.check("F6/F14 sales tax: round(gross x 0.07) per business per turn", f6)

    def f7():
        p = f7_buy_probability(200, 240, "loyal")               # spec example
        near(p, (1 - (200 / 240) ** 2) * 1.10)
        assert f7_buy_probability(240, 240, "bargain") == 0.0
        assert f7_buy_probability(500, 240, "premium") == 0.0
        assert f7_buy_probability(0, 240, "loyal") == 1.0       # clamped from 1.10
        assert f7_customer_max_price_cents("premium", 1.5) == 600
        raises(f7_buy_probability, 100, 0, "loyal")
    c.check("F7 buy chance: 1-(p/max)^2 x loyalty, clamped to [0,1]", f7)

    def f8():
        table = {4: 3, 5: 4, 6: 5, 7: 5, 8: 6, 9: 7, 10: 7}     # authoritative spec table
        assert {n: f8_required_correct(n) for n in table} == table
        assert f8_quiz_passed(4, 5) and not f8_quiz_passed(3, 5)
    c.check("F8 quiz: matches the spec table 4->3 ... 10->7 (integer ceiling)", f8)

    def f9_f10_f17():
        assert f9_holding_value_cents(0, 5_000_000) == 0
        change, cash, wallet = f10_trade("buy", 1_000_000, 1_234_567, 100000, 4321)
        assert (change, cash, wallet) == (-124, 99876, 4321)    # 123.4567c rounds UP
        change, cash, wallet = f10_trade("sell", 1_000_000, 1_234_567, 0, 4321)
        assert (change, cash, wallet) == (123, 123, 4321)       # rounds DOWN
        raises(f10_trade, "buy", 1, 1_000_000, 100000, 0)       # 0.0001c notional
        raises(f10_trade, "buy", 0, 1_000_000, 100000, 0)
        raises(f10_trade, "buy", 2_000_000_000, 1_000_000, 100000, 0)  # $2,000 > cash
        _, cash, wallet = f10_trade("buy", 100_000_000, 1_000_000, 100000, 777)  # $100 buy
        assert cash == 90000 and wallet == 777
        assert f17_paper_portfolio_value(100000, []) == 100000
        assert f17_paper_portfolio_value(50000, [(2_500_000, 10_000_000)]) == 52500
    c.check("F9/F10/F17 stocks: buy ceil, sell floor, <1c rejected, wallet unchanged", f9_f10_f17)

    def f11():
        assert f11_coach_question_allowed(9, "free") and not f11_coach_question_allowed(10, "free")
        assert f11_coach_question_allowed(29, "premium") and not f11_coach_question_allowed(30, "premium")
    c.check("F11 coach cap: free 10/day, premium 30/day", f11)

    def f12():
        assert f12_units_sold([True, True, True, True], 2) == 2  # spec example
        assert f12_units_sold([], 5) == 0
        assert f12_units_sold([True, False, True], 0) == 0
    c.check("F12 units sold = min(demand, stock or job capacity)", f12)

    c.check("F13 revenue: price x units summed over customer types",
            lambda: assert_eq(f13_gross_revenue(250, {"bargain": 1, "loyal": 3, "premium": 0}), 1000))

    def f15():
        assert f15_base_unit_cost_cents(200, "make") == 60       # Sticker Shop $2.00 x 30%
        assert f15_base_unit_cost_cents(4000, "resell") == 2600
        assert f15_base_unit_cost_cents(400, "service") == 0
        assert [f15_bulk_discount(n) for n in (24, 25, 99, 100)] == \
            [D("0"), D("0.05"), D("0.05"), D("0.10")]
        assert f15_restock_cash_debit(10, 60, False) == 600
        assert f15_restock_cash_debit(25, 30, True) == 641       # 750 x .95 x .90 = 641.25
        raises(f15_bulk_discount, 1001)
        assert f15_inflation_adjusted_unit_cost(100, 0.05) == 102  # clamped to +2%
        assert f15_inflation_adjusted_unit_cost(100, -0.05) == 98
        assert f15_inflation_adjusted_unit_cost(60, 0.004) == 60   # 60.24 -> 60
        lots = [[2, 50], [5, 60]]
        assert f15_fifo_cogs(lots, 3) == 160 and lots == [[0, 50], [4, 60]]
        assert f15_online_platform_fee(12800) == 1024
        assert f15_physical_monthly_bill(30, True) == 1800
        assert f15_physical_monthly_bill(30, False) == 0
        assert f15_physical_monthly_bill(29, True) == 0
        assert f15_business_contribution(10000, 700, 3000, 800, 0) == 5500
    c.check("F15 costs: cost ratios, bulk/supplier discounts, CPI clamp, FIFO COGS, fees", f15)

    def f16():
        assert f16_break_even_units(300, 90, 21, 1800) == 10     # ceil(1800/189)
        assert f16_break_even_units(100, 100, 7, 1800) is None
        assert f16_break_even_units(300, 90, 21, 0) == 0
    c.check("F16 break-even (Stretch): ceil(fixed / unit contribution)", f16)

    def f18_f21_f22():
        assert f18_lesson_reward(True, False) == 10
        assert f18_lesson_reward(True, True) == 0
        assert f18_lesson_reward(False, False) == 0
        assert f21_premium_checkout() == {"display_price_cents": 1000, "charged_cents": 0,
                                          "payment_processor_called": False}
        assert f22_starting_cash(True, False) == 10000
        assert f22_starting_cash(True, True) == 0
        assert f22_starting_cash(False, False) == 0
    c.check("F18/F21/F22 once-only rewards, $10 display / $0 charge, $100 starting cash", f18_f21_f22)

    def f19():
        ok, est = f19_coach_call_allowed(1000, 1.00, 4.00, 19.99, 0, True, True)
        assert est == D("0.004") and ok
        assert not f19_coach_call_allowed(1000, 1.00, 4.00, 19.999, 0, True, True)[0]
        assert not f19_coach_call_allowed(1000, 1.00, 4.00, 0, 0, True, False)[0]  # stale pricing
        assert not f19_coach_call_allowed(1000, 1.00, 4.00, 0, 0, False, True)[0]  # daily cap
    c.check("F19 coach budget: reserve estimate <= $20 - actual - pending, fail closed", f19)

    def f20():
        ledger = [("business_receipts", 5000), ("inventory_purchase", -1200),
                  ("rent_utilities", -1200), ("loan_interest", -67), ("loan_principal", -1639),
                  ("overdraft_fee", -500)]
        r = f20_money_report(10000, 10394, ledger, {
            "b2": (900, "cat-02", "2026-01-02T00:00:00Z"),
            "b1": (900, "cat-01", "2026-01-03T00:00:00Z")})
        assert r["wallet_net_change"] == 394
        assert r["cost_of_debt"] == 567                          # principal excluded
        assert r["biggest_drain"] == "inventory_purchase"        # tie -> supplies first
        assert r["top_earner"] == "b1"                           # tie -> lowest catalog ID
        empty = f20_money_report(0, 0, [], {})
        assert empty == {"wallet_net_change": 0, "cost_of_debt": 0,
                         "biggest_drain": None, "top_earner": None}
        raises(f20_money_report, 0, 1, [], {})
    c.check("F20 Money Report: reconciles, cost of debt, tie-break rules", f20)

    def f23():
        p, b = LOANS["personal"], LOANS["business"]
        assert f23_scheduled_payment(p["principal_cents"], p["apr"], 6) == 863   # $8.63
        assert f23_scheduled_payment(b["principal_cents"], b["apr"], 6) == 1706  # $17.06
        rows = f23_amortization(b["principal_cents"], b["apr"], 6)
        assert rows[0]["interest"] == 67 and rows[0]["principal"] == 1639       # spec example
        assert rows[-1]["closing"] == 0 and [r["turn"] for r in rows] == [30, 60, 90, 120, 150, 180]
        assert all(r["interest"] + r["principal"] == r["installment"] for r in rows)
        assert f23_amortization(p["principal_cents"], p["apr"], 6)[-1]["closing"] == 0
        assert f23_early_payoff(10000, D("0.08"), 15) == 10033                  # 33.33c interest
    c.check("F23 loans: $8.63 / $17.06 payments, first split 67c + $16.39, ends at $0", f23)

    def f24():
        assert f24_monthly_interest(10000, "basic") == 8                         # spec: $0.08
        assert f24_monthly_interest(10000, "locked") == 25
        lots = [LockedLot(10, 5000, 30), LockedLot(50, 3000, 10), LockedLot(200, 9000)]
        raises(f24_locked_withdraw, lots, 100, 99)                               # nothing matured
        assert f24_locked_withdraw(lots, 5010, 140) == 5010
        assert (lots[0].principal, lots[0].interest, lots[1].principal) == (0, 20, 3000)
        raises(f24_locked_withdraw, lots, 3031, 140)                             # lot 3 locked
    c.check("F24 savings: $100 basic -> 8c/month; locked lots mature at +90 turns, FIFO", f24)

    fixture = load_consumer_fixture()

    def f25():
        assert sum(len(r) for r in POOL.values()) == 100
        assert all(rng01(k) == fixture.rng01(k) for k in (["a"], ["2.8.3", "x", 7, "event-tier"]))
        a, b = fixture.BUSINESSES[0], fixture.BUSINESSES[12]
        ids = [(fixture.business_id(r[0].lower().replace(" ", "-")), r[4]) for r in (a, b)]
        mine = f25_assign_visitors_for_turn(fixture.VERSION, fixture.ACCOUNT, 7, ids)
        theirs = fixture.assign_agents_for_turn([(a[0], a[4]), (b[0], b[4])], 7)
        assert mine == theirs
        agents = [row[2] for row in mine]
        assert len(agents) == len(set(agents))
        assert all(agent in POOL[ctype] for _, _, agent, ctype in mine)
    c.check("F25 shopper pool: 40/40/20, unique per turn, matches consumer_agents_reference.py", f25)

    def f26():
        r = f26_purchase_probability(120, 240, "loyal", 1.20, 0.50)              # spec example
        near(r["p_source"], 0.75); near(r["p_price"], 0.75); near(r["p_buy"], 0.825)
        near(f26_purchase_probability(120, 240, "bargain", 0.30, 0.5)["p_price"], 0.930605)
        near(f26_purchase_probability(120, 240, "bargain", 3.00, 0.5)["p_price"], 0.487139)
        assert f26_purchase_probability(0, 240, "bargain", 1.2, 0.5)["p_source"] == 1
        assert f26_purchase_probability(240, 240, "loyal", 1.2, 1.0)["p_buy"] == 0
        near(f26_purchase_probability(0, 240, "loyal", 1.2, 0)["m_rel"], 0.90)
        near(f26_purchase_probability(0, 240, "loyal", 1.2, 1)["m_rel"], 1.10)
        assert f26_purchase_probability(0, 240, "loyal", 1.2, 1)["p_buy"] == 1.0  # clamped
        raises(f26_purchase_probability, 100, 0, "loyal", 1.2, 0.5)
        prev = 2.0
        for price in range(0, 241):                                               # monotone in price
            p = f26_purchase_probability(price, 240, "premium", 1.2, 0.5)["p_buy"]
            assert p <= prev + 1e-15
            prev = p
    c.check("F26/M2 purchase chance: worked example 0.825, epsilon bounds, edge cases", f26)

    def f27():
        assert f27_relationship_next(0.50, +1) == 0.52
        assert f27_relationship_next(0.0, -1) == 0.0 and f27_relationship_next(1.0, +1) == 1.0
        prob = f26_purchase_probability(120, 240, "loyal", 1.20, 0.50)
        near(f27_epsilon_gradient(prob, 1.20), -0.197781)                          # spec example
        near(f27_epsilon_next(prob, 1.20, 1), 1.198269)
        near(f27_epsilon_next(prob, 1.20, 0), 1.208158)
        edge = f26_purchase_probability(0, 240, "loyal", 1.20, 0.50)              # P_source = 1
        assert f27_epsilon_next(edge, 1.20, 0) == 1.20
        assert f27_epsilon_next(prob, 0.30, 1) >= 0.30
        # Same numbers as the consumer-agent oracle's own gradient check:
        near(f27_epsilon_gradient(prob, 1.20), -0.19778142481059938, 1e-12)
    c.check("F27/M4 learning: relationship +/-0.02; epsilon 1.198269 / 1.208158", f27)

    def m1():
        s, ok = m1_product_score(300, 500, 0.80, 0.50)
        near(s, 0.60); assert ok
        assert m1_product_score(600, 500, 0.8, 0.5) == "over_budget"
        assert m1_product_score(10, 0, 0.8, 0.5) == "over_budget"
        near(m1_product_score(500, 500, 0.8, 0.5)[0], 0.40)                       # p = B
    c.check("M1 product score: 0.60 example; B=0 and p>B are over_budget", m1)

    def m3():
        p = m3_business_probabilities({"a": 1.2, "b": 0.5, "c": 0.8})
        near(p["a"], 0.48); near(p["b"], 0.20); near(p["c"], 0.32)
        near(m3_business_probabilities({"a": 1.2, "b": 0.5, "c": 0.8}, "a")["a"], 0.61)
        assert m3_business_probabilities({"a": 0, "b": 0}) == "no_eligible_business"
    c.check("M3 business choice: 0.48/0.20/0.32; last-happy 0.61", m3)

    def m5():
        assert m5_spawn_probability(100, 20000) == 0.001
        assert m5_spawn_probability(500, 20000) == 0 and m5_spawn_probability(10, 0) == 0
        near(m5_child_trait(0.50, 0.04, 0, 1), 0.52)
        assert m5_child_transfer(10000) == 500
    c.check("M5 children: spawn 0.001, trait 0.52, 5% transfer = 500c", m5)

    def m6():
        assert m6_daily_budget(10000, 2000) == 4000
        assert m6_daily_budget(0, 0) == 0 and m6_daily_budget(0, 1000) == 1000
    c.check("M6 daily budget: 10,000c + 2,000c income -> 4,000c", m6)

    def m7():
        h, _, _ = m7_needs(0.50, 0, 0, 6, 0, 1, 0, 0)
        _, t, _ = m7_needs(0, 0.40, 0, 6, 0, 0, 1, 0)
        _, _, s = m7_needs(0, 0, 0.30, 6, 2, 0, 0, 0.80)
        near(h, 0.19); near(t, 0.11); near(s, 0.36)
        raises(m7_needs, 0, 0, 0, 20, 5, 0, 0, 1)
        raises(m7_urgency, 0.5, 1.0)
        near(m7_urgency(0.775, 0.55), 0.5)
    c.check("M7 needs: hunger .19, thirst .11, sleep .36; urgency", m7)

    def m8():
        r = m8_mood([.8, 1, .6, .8, .7, .9, 1, .8], [.15, .10, .15, .15, .15, .10, .05, .15],
                    0.60, 0.25, 1.20)
        near(r["target"], 0.795); near(r["mood"], 0.60975)
        near(r["lambda_eff"], 0.260975); near(r["epsilon_eff"], 1.14732)
        raises(m8_mood, [1], [0.9], 0.5, 0.25, 1.2)
    c.check("M8 mood: target .795, next .60975, lambda .260975, epsilon 1.14732", m8)

    def m9():
        hz, p = m9_departure(1800)
        near(hz, 0.001); near(p, 0.0009995)
        hz, p = m9_departure(3650)
        near(hz, 0.0404473); near(p, 0.0396402)
        assert m9_departure(100, 0)[1] == 0
        raises(m9_departure, -1)
    c.check("M9 departure: H .001 at a0; .0404473 / .0396402 at 3,650 days", m9)

    def m10():
        near(m10_move_probability(6000, 10000, 7), 0.10)
        assert m10_move_probability(6000, 10000, 6) == 0
        assert m10_move_probability(100, 0, 7) == 0.50
        assert m10_move_probability(0, 0, 7) == 0
    c.check("M10 housing: rent 6,000 / income 10,000 -> P_move .10", m10)

    def m11():
        assert m11_walk_away(200, 0, 0, 200, 350) == 200
        assert m11_walk_away(200, 0.5, 0.5, 200, 350) == 200     # 195 clamped up
        assert m11_accept_probability(200, 200) == 1.0
        near(m11_accept_probability(190, 200), 0.50)
        assert m11_accept_probability(180, 200) == 0.0 or abs(m11_accept_probability(180, 200)) < 1e-12
        assert m11_accept_probability(170, 200) == 0.0
        raises(m11_walk_away, 200, 0, 0, 0, 350)
    c.check("M11 negotiation: 200c -> 1, 190c -> .50, 180c/170c -> 0", m11)

    def m12():
        young, old = m12_age_profile(0), m12_age_profile(3650)
        assert young["initial_funds"] == 7500 and old["initial_funds"] == 12500
        near(young["epsilon_age"], 1.44); near(old["epsilon_age"], 0.96)
        near(young["lambda_age"], 0.1875); near(old["lambda_age"], 0.3125)
        near(young["daily_share"], 0.20); near(old["daily_share"], 0.10)
        raises(m12_age_profile, 3651)
    c.check("M12 age profile: 7,500c/1.44/.1875/.20 and 12,500c/.96/.3125/.10", m12)

    def m13():
        interest, eps = m13_craving(1.00, 1.20)
        near(interest, 1.20); near(eps, 1.14)
        near(0.60 * m13_food_multiplier(12), 0.75)
        assert [m13_food_multiplier(h) for h in (6, 7, 9, 10, 11, 14, 15, 17, 20, 21)] == \
            [1, 1.15, 1.15, 1, 1.25, 1.25, 1, 1.20, 1.20, 1]
        assert [m13_drink_multiplier(h) for h in (9, 10, 19, 20)] == [1, 1.15, 1.15, 1]
    c.check("M13 cravings and meal times: 1.20 / 1.14; lunch .60 -> .75", m13)

    def m14():
        near(m14_job_score(0.8, 0.9, 0.7), 0.80)
        near(m14_reliability(0.2, 0.3, 0.1, 0.9, 0.7), 0.900)
        assert m14_weekly_pay(200, 45) == 9500
        assert m14_weekly_pay(200, 0) == 0
        raises(m14_weekly_pay, 200, 61)
        assert 0 <= m14_effective_skill(1, 1, 1) <= 1
        near(m14_job_morale(1, 1, 1), 1.0)
    c.check("M14 jobs: score .80, reliability .900, 45 hours at $2 -> 9,500c", m14)

    def m15():
        assert m15_departure_transfer(2350) == (-2350, 2350)
        assert sum(m15_departure_transfer(2350)) == 0
        assert m15_deprivation_days(6, 0, 0, 0, 1) == 7
        assert m15_deprivation_days(6, 100, 0.2, 0.2, 0.9) == 0
    c.check("M15 departure: 2,350c to City Reserve nets to zero; 7-day deprivation", m15)

    def m16():
        near(m16_injury(0.80), 0.70); near(m16_rest(0.70), 0.90)
        assert m16_injury(0.05) == 0 and m16_rest(0.95) == 1
    c.check("M16 injury: .80 -> .70, rest -> .90, bounded to [0,1]", m16)

    return c.results


def assert_eq(actual, expected) -> None:
    assert actual == expected, f"{actual} != {expected}"


if __name__ == "__main__":
    results = run_checks()
    print("SPENDLY ENGINE FORMULA REFERENCE CHECKS (SPEC v2.8.6; reference model only,"
          " not application runtime tests)")
    for name, status in results:
        print(f"- {name}: {status}")
    failed = [r for r in results if r[1] != "PASS"]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    raise SystemExit(1 if failed else 0)
