# Spendly — Engine Variables and Expressions

Every variable name and every expression from `Spendly_Engine_Expressions.md`, written as plain text so it can be
read next to code. Where the spec gives a variable name (shown in `backticks`), that name is used in the expression.
Where the spec gives no name, the math symbol from `Spendly_Engine_Expressions.md` is kept as-is — no new names are
invented here.

`SPEC.md` is the rulebook. If this file and `SPEC.md` disagree, `SPEC.md` wins.

## How to read the expressions

| Written as | Means |
|---|---|
| `clamp(x, a, b)` | `min(max(x, a), b)` — keep x between a and b |
| `round(x)` | `round_half_away_to_cent` — round half away from zero to the nearest cent |
| `ceil(x)` / `floor(x)` | Round up / round down to a whole number |
| `sum(x)` | Add up every x |
| `x ^ y` | x to the power y |
| `ln(x)` | Natural log |
| `t` | Simulated turn (1 turn = 1 day; month = 30 turns; week = 7 turns) |
| `week(t) = ceil(t / 7)` | Seven-turn week index (turns 1–7 → week 1, 8–14 → week 2, …) |
| `rng01` / `u` | Deterministic seeded random draw in [0, 1) (Appendix A.14.1) |
| ¢ | Cents. All money is stored as whole cents ($1 = 100¢) |

---

## Engine formulas F1–F27 (SPEC.md Section 4)

### F1. Wallet balance from the tagged ledger — MVP · Ethan

```
W_t+1 = W_t + sum(c_i for i in L_t) - sum(d_i for i in L_t)
```

Every ledger entry carries a tag. Stock trades never change the wallet.

| Variable | Meaning | Value / unit |
|---|---|---|
| `W_t` | Wallet balance at start of turn t | ¢ |
| L_t | Ledger entries posted in turn t | |
| c_i | Credit (inflow) entry | ¢ |
| d_i | Debit (outflow) entry | ¢ |

### F2. Overdraft fee — MVP · Ethan

```
# on any wallet debit (including setup and second-slot debits outside a turn)
if balance_before >= 0 and balance_after < 0:
    pending_overdraft_crossing = 1
    pending_crossing_effective_turn = effective_turn_number

# at the overdraft-fee stage of effective_turn_number
if pending_overdraft_crossing == 1 and last_overdraft_fee_week != week(effective_turn_number):
    fee = FEE_OVERDRAFT                     # $5
    last_overdraft_fee_week = week(effective_turn_number)
else:
    fee = 0
pending_overdraft_crossing = 0              # after the fee stage, charged or weekly-capped
```

At most one fee per seven-turn week. Ending at exactly $0 does not set the flag; the fee itself cannot create a new crossing.

| Variable | Meaning | Value / unit |
|---|---|---|
| `pending_overdraft_crossing` | Pending overdraft crossing flag (`Wallet.pending_overdraft_crossing`) | 0 or 1 |
| `pending_crossing_effective_turn` | Effective turn of the pending crossing (`Wallet.pending_crossing_effective_turn`) | turn |
| `balance_before`, `balance_after` | Balance before / after the debit | ¢ |
| `effective_turn_number` | Effective turn of the posting | turn |
| `last_overdraft_fee_week` | Week of the last fee charged | week |
| `FEE_OVERDRAFT` | Overdraft fee | $5 |

### F3. Negative-balance interest — MVP · Ethan

```
r_week = r_annual / 52
interest_charge = round(abs(end_of_turn_negative_balance) * r_week)   # on turns 7, 14, 21, … when W_end < 0; posted as a wallet debit
```

Test case: an end-of-turn balance of −$100 at turn 7 gives `interest_charge = $0.23`.

| Variable | Meaning | Value / unit |
|---|---|---|
| `interest_charge` | Interest charge | ¢ |
| `W_end` / `end_of_turn_negative_balance` | End-of-turn balance (charged only when negative) | ¢ |
| `r_annual` | Annual negative-balance rate | 0.12 (12%) |
| `r_week` | Weekly rate | 0.12 / 52 |

### F4. Fresh Start threshold and wallet reset — MVP · Ethan

```
if end_of_turn_wallet_cents <= -20000 and fresh_start_uses_consumed < current_entitlement_limit:
    credit_cents = -end_of_turn_wallet_cents     # posted atomically as fresh_start_credit
    fresh_start_uses_consumed = fresh_start_uses_consumed + 1
    end_of_turn_wallet_cents = 0
# otherwise no reset
```

A balance of exactly −$200 triggers Fresh Start.

| Variable | Meaning | Value / unit |
|---|---|---|
| `end_of_turn_wallet_cents` | End-of-turn wallet | ¢ |
| `credit_cents` | Fresh Start credit | ¢ |
| `fresh_start_uses_consumed` | Lifetime uses consumed | uses |
| `current_entitlement_limit` | Entitlement limit | Free 3; Premium 5 |

### F5. Chance-event trigger, tier draw, and no-repeat deck — MVP · Ethan

```
event = 1 if u1 < P_event else 0             # P_event = 0.10; u1 uses A.14.1 key "event-trigger"

# tier_roll = u2, A.14.1 key "event-tier"
tier = Common    if tier_roll < 0.60
tier = Uncommon  if 0.60 <= tier_roll < 0.90
tier = Rare      if tier_roll >= 0.90

card = draw(D_tier minus U_tier)             # unused card IDs sorted lexicographically; mark card used
```

Card effects come from Appendix A.4. A tier deck resets only after every card in it has fired.

| Variable | Meaning | Value / unit |
|---|---|---|
| u1, `tier_roll` (u2) | Seeded trigger and tier rolls | [0, 1) |
| P_event | Event chance per turn | 0.10 |
| P_C, P_U, P_R | Tier chances given an event | 0.60 / 0.30 / 0.10 |
| N_C, N_U, N_R | Cards per tier | 7 / 4 / 2 |
| D_tier, U_tier | Cards in the tier deck / cards already used | |

### F6. Sales tax — MVP · Ethan

```
sales_tax = TAX_RATE * taxable_business_sales    # paid by the business; rounded to cents once when posted
```

| Variable | Meaning | Value / unit |
|---|---|---|
| `sales_tax` | Sales tax | ¢ |
| `TAX_RATE` | Sales tax rate | 0.07 (7%) |
| `taxable_business_sales` | Taxable business sales | ¢ |

### F7. Customer buy chance — MVP · Ethan

```
customer_max_price = base_customer_maximum * business_price_scale
P_base = 1 - (selling_price / customer_max_price) ^ 2
P_adj  = clamp(P_base * loyalty_multiplier, 0, 1)
```

A price at or above `customer_max_price` gives zero probability.

| Variable | Meaning | Value / unit |
|---|---|---|
| `selling_price` | Selling price | $0.01 to 2.00 × Premium Buyer max |
| `base_customer_maximum` | Customer type base maximum | Bargain $1.00; Loyal $2.40; Premium $4.00 |
| `business_price_scale` | Catalog price scale | Per template, Appendix A.2 |
| `customer_max_price` | Customer max price | $/unit |
| `loyalty_multiplier` | Loyalty multiplier | Loyal Regular 1.10; others 1.00 |
| P_base, P_adj | Base / adjusted buy probability | [0, 1] |

### F8. Quiz pass threshold — MVP · Kevin

```
required_correct = ceil(0.70 * question_count)
pass = correct_answers >= required_correct
```

MVP lessons and stock-event mini-lessons use `question_count = 5`, so `required_correct = 4`.

| Variable | Meaning | Value / unit |
|---|---|---|
| `question_count` | Questions in the quiz | 5 |
| `correct_answers` | Correct answers | |
| `required_correct` | Required correct | 4 |

### F9. Stock holding value — MVP · Ethan

```
holding_value   = fractional_shares * P_stock
portfolio_value = sum(holding_value for each holding)
```

| Variable | Meaning | Value / unit |
|---|---|---|
| `fractional_shares` | Fractional shares held | shares |
| `P_stock` | Current simulated share price | $/share |
| `holding_value` | Holding value | $ |
| `portfolio_value` | Portfolio value | $ |

### F10. Paper-trading cash and buy/sell isolation — MVP · Ethan

```
notional_cents_exact = shares_micros * execution_price_micros / 10^10    # requires notional_cents_exact >= 1.00
purchase_cost_cents = ceil(notional_cents_exact)     # a buy never rounds down
sale_proceeds_cents = floor(notional_cents_exact)    # a sale never rounds up
paper_account_cash_after = paper_account_cash_before - purchase_cost_cents + sale_proceeds_cents
wallet_after_stock_trade = wallet_before_stock_trade # stock trades never touch the wallet
```

| Variable | Meaning | Value / unit |
|---|---|---|
| `shares_micros` | Shares in micro-units | |
| `execution_price_micros` | Execution price in micro-units | |
| `notional_cents_exact` | Exact notional | ¢ |
| `purchase_cost_cents`, `sale_proceeds_cents` | Purchase cost / sale proceeds | ¢ |
| `paper_account_cash` | Paper-account cash | Starts at $1,000 |
| `wallet_before_stock_trade`, `wallet_after_stock_trade` | Game wallet before / after a paper trade | ¢ (always equal) |

### F11. Daily AI Coach question cap — MVP · Ethan

```
allow = questions_used_today < daily_plan_cap
```

If allowed, the question goes ahead (subject to moderation and provider availability); otherwise the daily-cap state is shown.

| Variable | Meaning | Value / unit |
|---|---|---|
| `questions_used_today` | Questions used today | Resets 00:00 UTC |
| `daily_plan_cap` | Daily plan cap | Free 10; Premium 30 |

### F12. Seeded demand-to-units conversion — MVP · Ethan

```
# for visitor_index i = 0 … visitors_per_day - 1
type_i = Bargain  if u_type < 0.40
type_i = Loyal    if 0.40 <= u_type < 0.80
type_i = Premium  if u_type >= 0.80

agent_i = candidates[ min(floor(u_pick * len(candidates)), len(candidates) - 1) ]

purchase_intent_i = 1 if u_buy < P_buy_i else 0      # P_buy_i from F26

demand = sum(purchase_intent_i for i in 0 … visitors_per_day - 1)

q = min(demand, inventory_available)         # inventory business
q = min(demand, jobs_remaining_today)        # service business
```

Businesses are processed by UUID ascending and visitors by index ascending; candidate agent indexes are sorted with no shuffle.

| Variable | Meaning | Value / unit |
|---|---|---|
| `visitor_index` | Visitor index | 0 … V−1 |
| `visitors_per_day` | Visitors per day | Per business, Appendix A.2 |
| `u_type`, `u_pick`, `u_buy` | Seeded draws | [0, 1) |
| `candidates`, `len(candidates)` | Sorted candidate agents and their count | |
| `purchase_intent` | Purchase intent | 0 or 1 |
| `demand` | Demand | units |
| `inventory_available` | Inventory available | units |
| `jobs_remaining_today` | Jobs remaining today | jobs |
| q | Units or jobs sold | |

### F13. Gross business revenue — MVP · Ethan

```
revenue_by_customer_type[c] = selling_price_per_unit * q_c
gross_business_revenue      = sum(revenue_by_customer_type[c] for each customer type c)
```

| Variable | Meaning | Value / unit |
|---|---|---|
| `selling_price_per_unit` | Selling price per unit | $ |
| q_c | Units/jobs sold to customer type c | |
| `revenue_by_customer_type` | Revenue by customer type | $ |
| `gross_business_revenue` | Gross business revenue | $ |

### F14. Business sales tax posting — MVP · Ethan

```
sales_tax_expense[b] = round(0.07 * taxable_gross_sales[b])
# for each business b in ascending UUID order; one entry per turn when sales_tax_expense[b] > 0
```

| Variable | Meaning | Value / unit |
|---|---|---|
| `taxable_gross_sales` | Taxable gross sales of business b | ¢ |
| `sales_tax_expense` | Sales tax expense | ¢ |

### F15. Supply costs, operating costs, COGS, and business profit — MVP · Ethan

```
base_unit_cost               = cents(default_template_price * base_type_cost_ratio)
inflation_adjusted_unit_cost = round(previous_month_unit_cost * (1 + newly_observed_monthly_CPI_change))
                               # only a newly available CPI observation is applied; change clamped to ±2%

restock_order_subtotal = units_ordered * current_unit_cost
supplier_event_factor  = 0.90 if Supplier Discount fired this turn else 1.00
restock_cash_debit     = round(restock_order_subtotal * (1 - eligible_bulk_discount) * supplier_event_factor)

COGS = sum(units_sold_from_each_lot * that_lot.unit_cost_cents)    # oldest lots first (FIFO)
online_platform_fee[b] = round(gross_online_sales[b] * 0.08)        # one entry per business per turn
physical_monthly_bill  = 1800¢             # per active physical business on turns 30, 60, 90, …
employee_cost          = 0¢                # MVP

business_contribution = gross_sales - sales_tax - COGS - online_platform_fee - due_physical_monthly_bill - employee_cost
```

The wallet is debited when a starter or restock order is bought. COGS is recognized on sale and never debits the wallet a second time.

| Variable | Meaning | Value / unit |
|---|---|---|
| `default_template_price` | Default template price | $ |
| `base_type_cost_ratio` | Base-type cost ratio | Make 30%; Resell 65%; Service 0% (Big Build 35%, Stretch) |
| `base_unit_cost` | Base supply cost per stock unit | ¢/unit |
| `inflation_adjusted_unit_cost` | Unit cost this month | ¢/unit |
| `previous_month_unit_cost`, `current_unit_cost` | Last month's / current unit cost | ¢/unit |
| `newly_observed_monthly_CPI_change` | Newly observed monthly CPI change | fraction, clamped to ±2% |
| `units_ordered` | Units ordered | units |
| `restock_order_subtotal` | Restock order subtotal | ¢ |
| `eligible_bulk_discount` | Eligible bulk discount | 0 below 25; 5% for 25–99; 10% for 100+ |
| `supplier_event_factor` | Supplier event factor | 0.90 or 1.00 |
| `restock_cash_debit` | Restock cash debit | ¢ |
| `units_sold_from_each_lot`, `unit_cost_cents` | Units sold from a lot and that lot's unit cost | |
| `COGS` | Cost of units actually sold | ¢; zero for Service |
| `gross_online_sales`, `online_platform_fee` | Online gross sales / platform fee | 8% of online sales |
| `physical_monthly_bill` | Combined rent and utilities | 1800¢ per active physical business |
| `employee_cost` | Employee cost | 0 in MVP |
| `gross_sales`, `sales_tax` | Gross sales / sales tax (F13, F14) | ¢ |
| `business_contribution` | Business contribution | ¢ |

### F16. Break-even units and contribution margin — Stretch · Ethan

```
unit_contribution = p - v - t_u
break_even_units  = ceil(fixed_costs / unit_contribution)   if unit_contribution > 0
break_even_units  = infinity                                if unit_contribution <= 0   # no break-even at this price
```

| Variable | Meaning | Value / unit |
|---|---|---|
| p | Selling price per unit | $ |
| v | Variable cost per unit | $ |
| t_u | Sales tax per unit | $ |
| `unit_contribution` | Unit contribution | $ |
| `fixed_costs` | Fixed costs | $ |
| `break_even_units` | Break-even units | units |

### F17. Paper-trading portfolio valuation — MVP · Ethan

```
V_h = S_h * P_h
portfolio_holdings_value = sum(V_h for each holding)
paper_portfolio_value    = paper_cash + portfolio_holdings_value
# the wallet is a separate account and is not included
```

| Variable | Meaning | Value / unit |
|---|---|---|
| S_h | Fractional shares | shares |
| P_h | Latest valid simulated price | $/share |
| `portfolio_holdings_value` | Holdings value | $ |
| `paper_cash` | Paper cash | $ |
| `paper_portfolio_value` | Paper portfolio value | $ |

### F18. Learn reward paid once per lesson — MVP · Kevin

```
if quiz passed and g == 0:
    delta_points = 10; g = 1                # granted atomically
else:
    delta_points = 0                        # no duplicate reward
```

Badges unlock when Appendix A.7 criteria are met.

| Variable | Meaning | Value / unit |
|---|---|---|
| ΔPts | Points granted for the lesson | 10 |
| g | Reward already granted flag | 0 or 1 |

### F19. AI Coach cost reservation and monthly budget — MVP · Ethan

```
estimated_request_cost = n_in * r_in + n_out * r_out
available_budget       = 20.00 - C_actual - C_pend
call = cap_ok and pricing_current and estimated_request_cost <= available_budget
```

If allowed, reserve `estimated_request_cost` atomically, call the provider, then reconcile to actual cost. Otherwise reject and show the limit/unavailable state.

| Variable | Meaning | Value / unit |
|---|---|---|
| `estimated_request_cost` | Estimated request cost | $ |
| n_in, n_out | Estimated input / reserved output tokens | tokens |
| r_in, r_out | Input / output token rates | $/token |
| C_actual, C_pend | Month actual cost / pending reservations | $ |
| `available_budget` | Available budget | Cap B_AI = $20/month |

### F20. Month-end Money Report aggregates — MVP · Ethan

```
delta_W      = W_close - W_open
cost_of_debt = sum(I_loan) + sum(I_debt) + sum(F_OD)
Pi_b         = R_b - T_b - COGS_b - F_plat_b - B_rent_b - E_emp_b
top          = argmax over b of Pi_b
drain        = argmax over k of D_k
```

| Variable | Meaning | Value / unit |
|---|---|---|
| W_open, W_close | Opening / closing wallet | ¢ |
| `cost_of_debt` | Cost of debt | ¢ |
| I_loan, I_debt, F_OD | Loan interest, debt interest, overdraft fees | ¢ |
| Pi_b | Business contribution | ¢ |
| B_rent_b | Rent and utilities | ¢ |
| D_k | Actual wallet debits in expense category k | ¢ |

### F21. Spendly Premium MVP mock price — MVP · Kevin

```
P_prem = $10.00 / month
C_MVP  = $0.00                              # simulated entitlement; no payment processor is called
```

| Variable | Meaning | Value / unit |
|---|---|---|
| P_prem | Premium display price | $10.00/month |
| C_MVP | Actual charge in MVP | $0.00 |

### F22. One-time Lesson 0 starting-cash grant — MVP · Ethan

```
if Lesson 0 completed and g_0 == 0:
    G = +$100; g_0 = 1                      # one transaction, tag starting_cash
else:
    G = 0
```

| Variable | Meaning | Value / unit |
|---|---|---|
| G | Starting-cash credit to the wallet | $100 |
| g_0 | Grant already posted flag | 0 or 1 |

### F23. Loan amortization, monthly payment, and early payoff — MVP · Ethan

```
monthly_rate        = APR / 12
scheduled_payment   = round(principal * monthly_rate / (1 - (1 + monthly_rate) ^ (-term_months)))
monthly_interest    = round(opening_principal * monthly_rate)
principal_component = scheduled_payment - monthly_interest
closing_principal   = opening_principal - principal_component
final_payment       = opening_principal + monthly_interest     # if this is the last installment
```

Baselines (SPEC.md F23): personal loan $50, 12% APR, 6 months → $8.63/month; business loan $100, 8% APR, 6 months → $17.06/month.

| Variable | Meaning | Value / unit |
|---|---|---|
| `APR` | Annual percentage rate | Personal 0.12; business 0.08 (Appendix A.3) |
| `monthly_rate` | Monthly rate | `APR / 12` |
| `principal` | Original loan amount | Personal $50; business $100 |
| `term_months` | Number of installments | 6 |
| `scheduled_payment` | Fixed monthly installment | Personal $8.63; business $17.06 |
| `opening_principal`, `closing_principal` | Principal at start / end of the month | ¢ |
| `monthly_interest` | Interest component | ¢ |
| `principal_component` | Principal paid this month | ¢ |
| `final_payment` | Last installment (clears principal to zero) | ¢ |

### F24. Savings-jar interest and maturity — MVP · Ethan

```
I         = round(J_0 * APR / 12)
J_close   = J_close_before_interest + I
t_mat     = t_dep + 90
V_lot     = P_rem + I_rem
withdraw  = (type == basic) or (requested_amount <= sum(V_lot for matured lots))
```

Locked withdrawals use matured lots only, consuming principal then interest, FIFO.

| Variable | Meaning | Value / unit |
|---|---|---|
| J_0 | Jar balance at start of 30-turn period | ¢ |
| I | Monthly interest | ¢ |
| J_close′, J_close | Closing balance before / after interest | ¢ |
| t_dep, t_mat | Deposit turn / locked maturity turn | turn |
| P_rem, I_rem | Remaining principal / interest in a lot | ¢ |
| `requested_amount` | Requested withdrawal | ¢ |

### F25. Persistent shopper pool and deterministic visitor assignment — MVP · Ethan

```
N_pool = 100
N_B = 40; N_L = 40; N_P = 20
V_t = sum(v_b for each active business b)
a   = A_type[ floor(u * n) ]                 # sorted unused agents of the drawn archetype; key "consumer-agent-assignment"
constraints: unique(t, b, i), unique(t, a)
```

| Variable | Meaning | Value / unit |
|---|---|---|
| N_pool | Pool size per player simulation | 100 |
| N_B, N_L, N_P | Bargain Hunter / Loyal Regular / Premium Buyer counts | 40 / 40 / 20 |
| v_b | Visitors per day of active business b | |
| V_t | Visitor opportunities in turn t | |
| A_type, n | Unused agents of the archetype and how many there are | |
| a | Assigned agent | |

### F26. Individual shopper purchase probability — MVP · Ethan

```
P_source = clamp(1 - (p / p_max) ^ 2, 0, 1)
P_price  = P_source ^ (epsilon / 1.20)
M_type   = 1.10 if archetype == LoyalRegular else 1.00
M_rel    = 0.90 + 0.20 * relationship_score
P_buy    = clamp(P_price * M_type * M_rel, 0, 1)
expected_demand = sum(P_buy for assigned visitor opportunities)
```

If `p_max <= 0`, the turn fails with a catalog/configuration error before dividing.

| Variable | Meaning | Value / unit |
|---|---|---|
| `p`, `p_max` | Price and archetype maximum after scale | ¢ |
| `epsilon` | Price-sensitivity exponent | [0.30, 3.00], default 1.20 |
| `relationship_score` | Relationship score | [0, 1], initial 0.50 |
| `M_type`, `M_rel` | Archetype and relationship modifiers | |
| `P_source`, `P_price`, `P_buy` | Source, individualized and final buy probability | [0, 1] |
| `expected_demand` | Expected demand | |

### F27. Shopper relationship and price-sensitivity learning — MVP · Ethan

```
experience_signal = +1     # fulfilled purchase
experience_signal = -1     # valid intent not fulfilled because stock or service capacity ran out
experience_signal =  0     # ordinary price/preference rejection

relationship_next = clamp(relationship + 0.02 * experience_signal, 0, 1)

M         = M_type * M_relationship
P_buy_raw = M * P_price
P_buy     = clamp(P_buy_raw, 0, 1)

dP_buy/d_epsilon = M * (P_price / 1.20) * ln(P_source)   # only when 0 < P_source < 1 and 0 < P_buy_raw < 1; otherwise 0

raw_epsilon_next = epsilon - 0.05 * (P_buy - observed_buy) * dP_buy/d_epsilon
step_limited     = clamp(raw_epsilon_next, epsilon * 0.95, epsilon * 1.05)
epsilon_next     = clamp(step_limited, 0.30, 3.00)
```

No epsilon update for closures, event suppression, or a stock/service-capacity stockout after intent. No learning is applied twice on a retry.

| Variable | Meaning | Value / unit |
|---|---|---|
| `relationship`, `relationship_next` | Relationship score now / next (`relationship_score`) | [0, 1] |
| `experience_signal` | Experience signal | +1, −1 or 0 |
| `M_relationship` | Relationship multiplier (`M_rel` in F26) | [0.90, 1.10] |
| `P_buy_raw` | Final probability before clamping | |
| `observed_buy` | Observed purchase | 1 bought, 0 rejected |
| `epsilon`, `raw_epsilon_next`, `step_limited`, `epsilon_next` | Price sensitivity now / before limits / after 5% step limit / next | [0.30, 3.00] |

---

## Simulated stock price (SPEC.md Appendix A.6)

Quotes update every five real-time minutes (288 ticks per day) in each player's own market world. Prices keep six
decimals internally and are rounded to cents for display only.

```
CPI_yoy_percent  = (CPI_t / CPI_t-12 - 1) * 100
delta_DFF_pp     = DFF_t - DFF_t-1                                   # percentage points
macro_daily_bias = clamp(-0.001 * delta_DFF_pp - 0.0005 * (CPI_yoy_percent - 2.0), -0.02, 0.02)
epsilon          ~ Uniform[-0.0005, 0.0005]    # from (market_seed, ticker, tick_timestamp), purpose "market-noise"
tick_return      = clamp(macro_daily_bias / 288 + epsilon, -0.005, 0.005)
next_price       = max($0.01, previous_price * (1 + tick_return))
```

Stock event multipliers apply after the normal tick update.

Note: in A.6, `epsilon` is the per-tick noise. It is **not** the shopper price-sensitivity `epsilon` from F26/F27.

| Variable | Meaning | Value / unit |
|---|---|---|
| CPI_t | FRED CPIAUCSL index, month t | |
| `CPI_yoy_percent` | CPI year-over-year percent | % |
| DFF_t | FRED Federal Funds Effective Rate | % |
| `delta_DFF_pp` | Change in DFF | pp |
| `macro_daily_bias` | Macro daily bias | [−0.02, 0.02] |
| `epsilon` (A.6) | Per-tick noise | |
| `tick_return` | Tick return | [−0.005, 0.005] |
| `market_seed`, `ticker`, `tick_timestamp` | Inputs to the seeded noise draw | |
| `previous_price`, `next_price` | Share price before / after the tick | $, floor $0.01; six decimals internally |
| 288 | Five-minute ticks per day | |

---

## Consumer-agent formulas M1–M16 (SPEC.md Appendix A.26 §5)

M2 and M4 are MVP and extend F26 and F27. The rest are Stretch, using proposed V2.8 defaults.

### M1. Product score and affordability — Stretch

```
over_budget = (B <= 0) or (p > B)           # checked before dividing
S      = wq * q + (1 - wq) * (1 - p / B)
accept = S >= theta
choice = argmax(S)                          # tie-break by stable product ID
```

| Variable | Meaning | Value / unit |
|---|---|---|
| p | Candidate product price | ¢ |
| B | Resident daily purchase budget | ¢ |
| q | Product quality rating | [0, 1] |
| `wq` | Resident quality weight | [0, 1], mean 0.50 |
| `theta` | Buy threshold | 0.35 |
| S | Product score | [0, 1] |

### M2. Spendly demand and individual price sensitivity — MVP

```
P_src   = clamp(1 - (p / p_max) ^ 2, 0, 1)
P_price = P_src ^ (epsilon / 1.20)
M_type  = 1.10 if Loyal Regular else 1.00
M_rel   = 0.90 + 0.20 * R
P_buy   = clamp(P_price * M_type * M_rel, 0, 1)
E[D]    = sum(P_buy_i for each visitor i)
```

The power law `D = D_0 * (p / p_ref) ^ (-epsilon)` is **not** used as a buying probability: it is undefined at
`p = 0` and can exceed the visitor count.

| Variable | Meaning | Value / unit |
|---|---|---|
| p, p_max | Posted price / archetype-business maximum | ¢ |
| `epsilon` | Price-sensitivity exponent | [0.30, 3.00], default 1.20 |
| R | Per-business relationship | [0, 1], initial 0.50 |
| M_type | Archetype modifier | 1.00 or 1.10 |
| M_rel | Relationship multiplier | [0.90, 1.10] |

### M3. Business choice (city routing) — Stretch

```
w_b     = I_b * A_b
P(b)    = w_b / sum(w_j for all j)
P(last) = lambda + (1 - lambda) * w_last / sum(w_j for all j)   # when the last-happy business is eligible
no visit if sum(w_j for all j) == 0
```

| Variable | Meaning | Value / unit |
|---|---|---|
| I_b | Resident interest in business b | ≥ 0, initial 1.00 |
| A_b | Business attractiveness | ≥ 0 |
| w_b | Business choice weight | |
| `lambda` | Return-to-last-happy probability | [0, 0.90], 0.25 |
| P(b) | Business selection probability | [0, 1] |

### M4. Preference learning: relationship and price sensitivity — MVP

```
R_next = clamp(R + eta_R * s, 0, 1)

M     = M_type * M_rel
P_raw = M * P_price
P_buy = clamp(P_raw, 0, 1)

dP_buy_d_epsilon = M * (P_price / 1.20) * ln(P_src)    # when 0 < P_src < 1 and 0 < P_raw < 1; otherwise 0

epsilon_raw  = epsilon - eta_epsilon * (P_buy - y) * dP_buy_d_epsilon
epsilon_next = clamp(clamp(epsilon_raw, epsilon * (1 - X), epsilon * (1 + X)), 0.30, 3.00)
```

No price-sensitivity update on closures, event suppression, stockout after intent, or service-capacity exhaustion.

| Variable | Meaning | Value / unit |
|---|---|---|
| R | Agent/business relationship score | [0, 1], initial 0.50 |
| s | Experience signal | −1, 0 or +1 |
| `eta_R` | Relationship step | 0.02 |
| `epsilon` | Price sensitivity | [0.30, 3.00] |
| `eta_epsilon` | Gradient learning rate | 0.05 |
| X | Max daily relative ε movement | 0.05 |
| y | Observed purchase result | 1 or 0 |

### M5. Child creation and bounded trait mutation — Stretch

```
P_spawn = 0                                                  # if population is at or above the cap
P_spawn = p_base * min(1, max(0, F) / F_ref)                 # otherwise; p_base = 0.001, F_ref = 10000¢
z       ~ TruncatedNormal(mean 0, sd 0.05, min -0.10, max 0.10)
w_child = clamp(w_parent * (1 + z), lower, upper)
F_child = round(0.05 * F_parent)            # moved from parent via two balanced city-ledger entries
```

| Variable | Meaning | Value / unit |
|---|---|---|
| F | Resident available funds | ¢ |
| `F_ref` | Funds reference | 10000¢ |
| `p_base` | Base daily spawn chance | 0.001 |
| z | Trait mutation (truncated normal) | [−0.10, 0.10] |
| w_parent, w_child | Inheritable trait of parent / child | |

### M6. Resident funds and daily purchase budget — Stretch

```
F_avail = max(0, F_0 + y_d)
B       = floor(min(F_avail, max(0, 0.20 * F_0 + y_d)))
```

| Variable | Meaning | Value / unit |
|---|---|---|
| F_0 | Opening funds before today's income | ¢ |
| y_d | Income today | ¢ |
| F_avail | Funds available today | ¢ |
| 0.20 | Discretionary share of opening funds | |
| B | Daily budget | ¢ |

### M7. Hunger, thirst, sleep, and urgency — Stretch

```
h_next = clamp(min(1, h + 0.04 * tau_a) - 0.55 * e_f, 0, 1)
t_next = clamp(min(1, t + 0.06 * tau_a) - 0.65 * e_d, 0, 1)
s_next = clamp(min(1, s + 0.05 * tau_a) - 0.15 * tau_s * Q_h, 0, 1)
U(n, g) = clamp((n - g) / (1 - g), 0, 1)    # for need n and trigger g < 1
```

Highest positive urgency goes first; ties resolve thirst, hunger, sleep, then discretionary choice.

| Variable | Meaning | Value / unit |
|---|---|---|
| h, t, s | Hunger, thirst, sleep need | [0, 1] |
| tau_a, tau_s | Hours awake / hours slept | hours/day |
| e_f, e_d | Ate / drank this period | 0 or 1 |
| Q_h | Home sleep quality | [0, 1] |
| g | Need priority trigger | thirst .45, hunger .55, sleep .65 |
| U | Urgency | [0, 1] |

### M8. Mood and derived behavior modifiers — Stretch

```
m_target    = sum(a_k * x_k for each driver k)
m_next      = clamp(m + 0.05 * (m_target - m), 0, 1)        # 0.05 = smoothing factor alpha
lambda_eff  = clamp(lambda * (0.8 + 0.4 * m), 0, 0.90)
epsilon_eff = clamp(epsilon * (1.2 - 0.4 * m), 0.30, 3.00)
```

Drivers x_k: funds ratio, job status, 1−h, 1−t, 1−s, health, craving met, home quality. Weights a_k sum to 1.

| Variable | Meaning | Value / unit |
|---|---|---|
| x_k | Normalized mood driver | [0, 1] |
| a_k | Driver weight | [0, 1] |
| m, m* | Prior mood / weighted mood target | [0, 1] |
| α | Smoothing factor | 0.05 |
| lambda_eff, epsilon_eff | Effective return loyalty / price sensitivity | |

### M9. Age hazard and departure — Stretch

```
H        = min(20, h_0 * e ^ (k * (age - a_0)))
P_depart = 1 - e ^ (-H * DeltaDays)
```

At the max-age limit the resident is marked retired regardless of the draw.

| Variable | Meaning | Value / unit |
|---|---|---|
| age | Fictional resident age | |
| h_0 | Base daily departure hazard | |
| k | Hazard growth coefficient | |
| a_0 | Reference age | |
| H | Capped hazard | ≤ 20 |
| `DeltaDays` | Elapsed simulation days | days |

### M10. Housing affordability and move choice — Stretch

```
a = rent / income        if income > 0
a = +infinity            if income == 0 and rent > 0
a = 0                    if rent == 0 and income == 0
P_move = clamp(0.05 + 0.50 * max(0, a - 0.50), 0.05, 0.50)   # after a > 0.50 for 7 consecutive days
target: a <= 0.35
```

Rent is due every 30 days with a 7-day grace period and one 200¢ late fee per unpaid cycle.

| Variable | Meaning | Value / unit |
|---|---|---|
| rent, income | Monthly rent / income | ¢ |
| a | Rent-to-income affordability ratio | |
| P_move | Move probability after the trigger | [0.05, 0.50] |

### M11. Job negotiation — Stretch

```
M        = clamp(M_0 * (1 - 0.20 * P + 0.15 * S), w_min, w_max)   # 0.20 = kappa, 0.15 = mu
w_ask    = clamp(1.10 * M_0, w_min, w_max)
P_accept = 1                       if O >= M
P_accept = 1 - (M - O) / (0.10 * M)  if 0.90 * M <= O < M
P_accept = 0                       otherwise
accept   = u < P_accept
```

| Variable | Meaning | Value / unit |
|---|---|---|
| M_0 | Expected role wage from posting | ¢/hour |
| P | Normalized financial/need pressure | [0, 1] |
| S | Normalized resident strength | [0, 1] |
| κ, μ | Pressure / strength coefficients | 0.20, 0.15 |
| M | Walk-away minimum | ¢/hour |
| O | Employer wage offer | ¢/hour |
| w_min, w_max | Posting wage limits | |

### M12. Age-linked resident behavior — Stretch

```
A             = clamp(age_days / 3650, 0, 1)
initial_funds = round(10000 * (0.75 + 0.50 * A))
epsilon_age   = clamp(epsilon * (1.20 - 0.40 * A), 0.30, 3.00)
lambda_age    = clamp(0.25 * (0.75 + 0.50 * A), 0, 0.90)
daily_share   = 0.20 - 0.10 * A
```

Mood factors from M8 apply afterwards.

| Variable | Meaning | Value / unit |
|---|---|---|
| `age_days` | Age in days | days |
| A | Normalized age | [0, 1] |
| `initial_funds` | Initial funds (F_0) | ¢ |
| `daily_share` | Daily spending share (σ_d) | |

### M13. Craving generation and meal-time demand — Stretch

```
craving starts if none is active and u < p_crave     # lasts 3 days
I_match_next = 1.20 * I_match
epsilon_next = clamp(0.95 * epsilon, 0.30, 3.00)

mu_food    = 1.15   07:00–09:59
mu_food    = 1.25   11:00–14:59
mu_food    = 1.20   17:00–20:59;  otherwise 1.00
mu_drink   = 1.15   10:00–19:59;  otherwise 1.00
mu_weather = 1.10   drinks during the Good Weather event

priority = U * mu_time * mu_weather
```

Priority affects choice order only and never bypasses available funds.

| Variable | Meaning | Value / unit |
|---|---|---|
| p_crave | Craving chance | |
| I_match | Interest in the craved product kind | |
| mu (mu_food, mu_drink, mu_weather, mu_time) | Time-of-day or weather multiplier | |
| U | Urgency from M7 | |

### M14. Job search and work reliability — Stretch

```
J         = 0.40 * f_w + 0.30 * f_h + 0.30 * f_k
rho_w     = clamp(1 - 0.20*s - 0.15*h - 0.20*t - 0.15*(1 - H) + 0.10*(m - 0.50), 0, 1)
k_eff     = clamp(k_0 * (0.90 + 0.20 * A) * rho_w, 0, 1)
J_morale  = 0.40 * sigma_w + 0.30 * f_h + 0.30 * m
Pay       = round(c_h * (min(n, 40) + 1.50 * max(0, n - 40)))    # hours n <= 60
```

| Variable | Meaning | Value / unit |
|---|---|---|
| f_w, f_h, f_k | Wage, hours and skill fit | [0, 1] |
| s, h, t | Sleep need, hunger, thirst | [0, 1] |
| H | Health | [0, 1] |
| m | Mood | [0, 1] |
| rho_w | Work reliability | [0, 1] |
| k_0, k_eff | Base / effective skill | [0, 1] |
| sigma_w | Wage satisfaction | [0, 1] |
| c_h | Hourly wage | ¢ |
| n | Weekly hours | ≤ 60 |

### M15. Departure and city-ledger transfer — Stretch

```
deprived = 1 if (F == 0 or h >= 0.95 or t >= 0.95 or H <= 0.10) else 0
d_next   = d + 1 if deprived == 1 else 0
moves away when d == 7
```

On departure or retirement the remaining funds move to `CITY_RESERVE` in one unique-key transaction.

| Variable | Meaning | Value / unit |
|---|---|---|
| δ (deprived) | Deprived today | 0 or 1 |
| F | Funds | ¢ |
| h, t, H | Hunger, thirst, health | [0, 1] |
| d | Consecutive deprivation days | days |
| `CITY_RESERVE` | City ledger account that receives departing funds | |

### M16. Injury and recovery state — Stretch

```
H_next  = clamp(H - 0.10, 0, 1)     # on a seeded daily injury draw u < 0.005; work hours x0.5 that day
C_treat = 200¢                      # if treatment is chosen and funds >= 200¢; otherwise 0
H_next  = clamp(H + 0.20, 0, 1)     # on a rest day
```

| Variable | Meaning | Value / unit |
|---|---|---|
| H | Health | [0, 1] |
| C_treat | Treatment debit | 200¢ |

---

## Index of named spec variables

Every variable that has a spec name, A–Z, with the formula(s) that use it.

| Spec name | Formula(s) |
|---|---|
| `age_days` | M12 |
| `APR` | F23, F24 |
| `available_budget` | F19 |
| `balance_after` | F2 |
| `balance_before` | F2 |
| `base_customer_maximum` | F7 |
| `base_type_cost_ratio` | F15 |
| `base_unit_cost` | F15 |
| `break_even_units` | F16 |
| `business_contribution` | F15 |
| `business_price_scale` | F7 |
| `candidates` | F12 |
| `CITY_RESERVE` | M15 |
| `COGS` | F15 |
| `correct_answers` | F8 |
| `cost_of_debt` | F20 |
| `CPI_yoy_percent` | A.6 |
| `credit_cents` | F4 |
| `current_entitlement_limit` | F4 |
| `customer_max_price` | F7 |
| `daily_plan_cap` | F11 |
| `daily_share` | M12 |
| `default_template_price` | F15 |
| `delta_DFF_pp` | A.6 |
| `DeltaDays` | M9 |
| `demand` | F12 |
| `effective_turn_number` | F2 |
| `eligible_bulk_discount` | F15 |
| `employee_cost` | F15 |
| `end_of_turn_negative_balance`, `W_end` | F3 |
| `end_of_turn_wallet_cents` | F4 |
| `epsilon` (A.6 per-tick noise) | A.6 |
| `epsilon` (price sensitivity) | F26, F27, M2, M4, M8, M12, M13 |
| `estimated_request_cost` | F19 |
| `eta_epsilon` | M4 |
| `eta_R` | M4 |
| `execution_price_micros` | F10 |
| `expected_demand` | F26 |
| `experience_signal` | F27 |
| `F_ref` | M5 |
| `FEE_OVERDRAFT` | F2 |
| `final_payment` | F23 |
| `fixed_costs` | F16 |
| `fractional_shares` | F9 |
| `fresh_start_uses_consumed` | F4 |
| `gross_business_revenue` | F13 |
| `gross_online_sales` | F15 |
| `holding_value` | F9 |
| `inflation_adjusted_unit_cost` | F15 |
| `initial_funds` | M12 |
| `interest_charge` | F3 |
| `inventory_available` | F12 |
| `jobs_remaining_today` | F12 |
| `lambda` | M3, M8 |
| `last_overdraft_fee_week` | F2 |
| `loyalty_multiplier` | F7 |
| `M_relationship` | F27 |
| `macro_daily_bias` | A.6 |
| `market_seed`, `ticker`, `tick_timestamp` | A.6 |
| `monthly_interest` | F23 |
| `monthly_rate` | F23 |
| `newly_observed_monthly_CPI_change` | F15 |
| `notional_cents_exact` | F10 |
| `observed_buy` | F27 |
| `online_platform_fee` | F15 |
| `opening_principal`, `closing_principal` | F23 |
| `p_base` | M5 |
| `P_buy_raw` | F27 |
| `P_source` | F26, F27 |
| `P_stock` | F9 |
| `paper_account_cash` | F10 |
| `paper_cash` | F17 |
| `paper_portfolio_value` | F17 |
| `pending_crossing_effective_turn` | F2 |
| `pending_overdraft_crossing` | F2 |
| `physical_monthly_bill` | F15 |
| `portfolio_holdings_value` | F17 |
| `portfolio_value` | F9 |
| `previous_month_unit_cost`, `current_unit_cost` | F15 |
| `previous_price`, `next_price` | A.6 |
| `principal` | F23 |
| `principal_component` | F23 |
| `purchase_cost_cents` | F10 |
| `purchase_intent` | F12 |
| `question_count` | F8 |
| `questions_used_today` | F11 |
| `r_annual` | F3 |
| `r_week` | F3 |
| `raw_epsilon_next`, `step_limited`, `epsilon_next` | F27 |
| `relationship_score` | F26, F27 |
| `relationship`, `relationship_next` | F27 |
| `requested_amount` | F24 |
| `required_correct` | F8 |
| `restock_cash_debit` | F15 |
| `restock_order_subtotal` | F15 |
| `revenue_by_customer_type` | F13 |
| `sale_proceeds_cents` | F10 |
| `sales_tax` | F6 |
| `sales_tax_expense` | F14 |
| `scheduled_payment` | F23 |
| `selling_price` | F7 |
| `selling_price_per_unit` | F13 |
| `shares_micros` | F10 |
| `supplier_event_factor` | F15 |
| `TAX_RATE` | F6 |
| `taxable_business_sales` | F6 |
| `taxable_gross_sales` | F14 |
| `term_months` | F23 |
| `theta` | M1 |
| `tick_return` | A.6 |
| `tier_roll` | F5 |
| `u_buy`, `u_pick`, `u_type` | F12 |
| `unit_contribution` | F16 |
| `units_ordered` | F15 |
| `visitor_index` | F12 |
| `visitors_per_day` | F12 |
| `W_t` | F1 |
| `wallet_after_stock_trade`, `wallet_before_stock_trade` | F10 |
| `wq` | M1 |
