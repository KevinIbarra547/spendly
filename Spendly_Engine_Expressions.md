# Spendly — Engine Expressions

Every formula in `SPEC.md` (KevinIbarra547/spendly), written in mathematical notation. Each formula has a **Where** table mapping every symbol back to the variable name used in the spec.

## Contents

1. [Notation](#1-notation)
2. [Engine formulas F1–F27](#2-engine-formulas-f1f27-section-4)
3. [Simulated stock price](#3-simulated-stock-price-appendix-a6)
4. [Consumer-agent formulas M1–M16](#4-consumer-agent-formulas-m1m16-appendix-a26-5)

## 1. Notation

These operators and conventions apply to every formula below. Conditions are written to the right of each equation.

| Symbol | Meaning | Note |
|---|---|---|
| $\mathrm{clamp}(x, a, b)$ | min(max(x, a), b): keeps x between a and b | Spec writes this both as clamp(x,lo,hi) and clamp(lo,hi,x); here it is always clamp(x, a, b) |
| $\mathrm{round}(x)$ | Round half away from zero to the nearest cent (`round_half_away_to_cent`) | Applied when a money entry is posted |
| $\lceil x\rceil$ | Ceiling: round up to the next whole number |  |
| $\lfloor x\rfloor$ | Floor: round down to the next whole number |  |
| $\sum_{i}{x_{i}}$ | Sum over all i |  |
| $t$ | Simulated turn (1 turn = 1 day) | Month M = 30 turns; week = 7 turns |
| $k(t)=\lceil t/7\rceil$ | Seven-turn week index (`week(t)`) | Turns 1–7 → week 1, 8–14 → week 2, … |
| $\text{¢}$ | Cents. All money is stored as whole cents | \$1 = 100¢ |
| $u$ | Deterministic seeded random draw in [0, 1) (`rng01`, Appendix A.14.1) |  |

## 2. Engine formulas F1–F27 (Section 4)

Ethan owns every engine formula and simulation number. Where Appendix A gives a later value, build to the Appendix value.

### F1. Wallet balance from the tagged ledger

*MVP · Owner: Ethan*

$$
\begin{aligned}
& W_{t+1}=W_{t}+\sum_{i\in L_{t}}{c_{i}}-\sum_{i\in L_{t}}{d_{i}}
\end{aligned}
$$

Every ledger entry carries a tag. Stock trades never change $W$.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $W_{t}$ | Wallet balance at start of turn t (`W_t`) | ¢ |
| $L_{t}$ | Ledger entries posted in turn t |  |
| $c_{i}$ | Credit (inflow) entry | ¢ |
| $d_{i}$ | Debit (outflow) entry | ¢ |

### F2. Overdraft fee

*MVP · Owner: Ethan*

$$
\begin{aligned}
& \chi \leftarrow 1 && \text{on any wallet debit where }W_{\mathrm{before}}\ge 0\text{ and }W_{\mathrm{after}}<0\text{ (including setup and second-slot debits outside a turn)} \\
& F_{\mathrm{OD}}=\$5 && \text{at the overdraft-fee stage of the effective turn }t_{e}\text{, if }\chi =1\text{ and }k_{\mathrm{last}}\ne k(t_{e}) \\
& F_{\mathrm{OD}}=0 && \text{otherwise} \\
& k_{\mathrm{last}}\leftarrow k(t_{e}) && \text{when the fee is charged} \\
& \chi \leftarrow 0 && \text{after the fee stage, whether charged or weekly-capped}
\end{aligned}
$$

At most one fee per seven-turn week. Ending at exactly \$0 does not set $\chi$, and the fee itself cannot create a new crossing.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $\chi$ | Pending overdraft crossing flag (`pending_overdraft_crossing`) | 0 or 1 |
| $W_{\mathrm{before}}, W_{\mathrm{after}}$ | Balance before / after the debit (`balance_before`, `balance_after`) | ¢ |
| $t_{e}$ | Effective turn of the posting (`effective_turn_number`) | turn |
| $k_{\mathrm{last}}$ | Week of the last fee charged (`last_overdraft_fee_week`) | week |
| $F_{\mathrm{OD}}$ | Overdraft fee (`FEE_OVERDRAFT`) | \$5 |

### F3. Negative-balance interest

*MVP · Owner: Ethan*

$$
\begin{aligned}
& I_{t}=\mathrm{round}(-W_{t}\times \frac{r}{52}) && \text{on turns }t=7,14,21,\ldots \text{ when }W_{t}<0\text{; posted as a wallet debit}
\end{aligned}
$$

Test case: $W_{7}=-\$100$ gives $I_{7}=\$0.23$.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $I_{t}$ | Interest charge (`interest_charge`) | ¢ |
| $W_{t}$ | End-of-turn negative balance | ¢ |
| $r$ | Annual negative-balance rate (`r_annual`) | 0.12 (12%) |
| $r/52$ | Weekly rate (`r_week`) | 0.12 / 52 |

### F4. Fresh Start threshold and wallet reset

*MVP · Owner: Ethan*

$$
\begin{aligned}
& C_{\mathrm{FS}}=-W_{t} && \text{if }W_{t}\le -20000\text{¢}\text{ and }n_{\mathrm{FS}}<N_{\mathrm{FS}}\text{ (posted atomically as }\texttt{fresh\_start\_credit}\text{)} \\
& n_{\mathrm{FS}}\leftarrow n_{\mathrm{FS}}+1 \\
& W_{t}\leftarrow 0
\end{aligned}
$$

Otherwise no reset. A balance of exactly −\$200 triggers Fresh Start.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $W_{t}$ | End-of-turn wallet (`end_of_turn_wallet_cents`) | ¢ |
| $C_{\mathrm{FS}}$ | Fresh Start credit (`credit_cents`) | ¢ |
| $n_{\mathrm{FS}}$ | Lifetime uses consumed (`fresh_start_uses_consumed`) | uses |
| $N_{\mathrm{FS}}$ | Entitlement limit (`current_entitlement_limit`) | Free 3; Premium 5 |

### F5. Chance-event trigger, tier draw, and no-repeat deck

*MVP · Owner: Ethan*

$$
\begin{aligned}
& E=1 && \text{if }u_{1}<P_{\mathrm{event}}=0.10\text{, otherwise }E=0\text{ (no event)} \\
& \mathrm{tier}=\mathrm{Common} && \text{if }u_{2}<0.60 \\
& \mathrm{tier}=\mathrm{Uncommon} && \text{if }0.60\le u_{2}<0.90 \\
& \mathrm{tier}=\mathrm{Rare} && \text{if }u_{2}\ge 0.90 \\
& \mathrm{card}=\mathrm{draw}(D_{\mathrm{tier}}\setminus U_{\mathrm{tier}}) && \text{unused card IDs sorted lexicographically; mark card used}
\end{aligned}
$$

$u_{1}$, $u_{2}$ use the A.14.1 "event-trigger" and "event-tier" keys. Card effects come from Appendix A.4. A tier deck resets only after every card in it has fired.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $u_{1}, u_{2}$ | Seeded trigger and tier rolls (`tier_roll`) | [0, 1) |
| $P_{\mathrm{event}}$ | Event chance per turn | 0.10 |
| $P_{C}, P_{U}, P_{R}$ | Tier chances given an event | 0.60 / 0.30 / 0.10 |
| $N_{C}, N_{U}, N_{R}$ | Cards per tier | 7 / 4 / 2 |
| $D_{\mathrm{tier}}, U_{\mathrm{tier}}$ | Cards in the tier deck / cards already used |  |

### F6. Sales tax

*MVP · Owner: Ethan*

$$
\begin{aligned}
& T=\tau \times S_{\mathrm{tax}}
\end{aligned}
$$

Paid by the business; rounded to cents once when the tax entry is posted.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $T$ | Sales tax (`sales_tax`) | ¢ |
| $\tau$ | Sales tax rate (`TAX_RATE`) | 0.07 (7%) |
| $S_{\mathrm{tax}}$ | Taxable business sales (`taxable_business_sales`) | ¢ |

### F7. Customer buy chance

*MVP · Owner: Ethan*

$$
\begin{aligned}
& p_{\mathrm{max}}=p_{\mathrm{base}}\times \sigma  \\
& P_{\mathrm{base}}=1-{(\frac{p}{p_{\mathrm{max}}})}^{2} \\
& P_{\mathrm{adj}}=\mathrm{clamp}(P_{\mathrm{base}}\times \ell , 0, 1)
\end{aligned}
$$

A price at or above $p_{\mathrm{max}}$ gives zero probability.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $p$ | Selling price (`selling_price`) | \$0.01 to 2.00 × Premium Buyer max |
| $p_{\mathrm{base}}$ | Customer type base maximum (`base_customer_maximum`) | Bargain \$1.00; Loyal \$2.40; Premium \$4.00 |
| $\sigma$ | Catalog price scale (`business_price_scale`) | Per template, Appendix A.2 |
| $p_{\mathrm{max}}$ | Customer max price (`customer_max_price`) | \$/unit |
| $\ell$ | Loyalty multiplier (`loyalty_multiplier`) | Loyal Regular 1.10; others 1.00 |
| $P_{\mathrm{base}}, P_{\mathrm{adj}}$ | Base / adjusted buy probability | [0, 1] |

### F8. Quiz pass threshold

*MVP · Owner: Kevin*

$$
\begin{aligned}
& n_{\mathrm{req}}=\lceil 0.70\times n_{Q}\rceil  \\
& \mathrm{pass} \iff  n_{c}\ge n_{\mathrm{req}}
\end{aligned}
$$

MVP lessons and stock-event mini-lessons use $n_{Q}=5$, so $n_{\mathrm{req}}=4$.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $n_{Q}$ | Questions in the quiz (`question_count`) | 5 |
| $n_{c}$ | Correct answers (`correct_answers`) |  |
| $n_{\mathrm{req}}$ | Required correct (`required_correct`) | 4 |

### F9. Stock holding value

*MVP · Owner: Ethan*

$$
\begin{aligned}
& V_{h}=S_{h}\times P_{h} \\
& V_{\mathrm{port}}=\sum_{h}{V_{h}}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $S_{h}$ | Fractional shares held (`fractional_shares`) | shares |
| $P_{h}$ | Current simulated share price (`P_stock`) | \$/share |
| $V_{h}$ | Holding value (`holding_value`) | \$ |
| $V_{\mathrm{port}}$ | Portfolio value (`portfolio_value`) | \$ |

### F10. Paper-trading cash and buy/sell isolation

*MVP · Owner: Ethan*

$$
\begin{aligned}
& N=\frac{s_{\mu }\times p_{\mu }}{10^{10}} && \text{exact notional in cents; requires }N\ge 1.00 \\
& C_{\mathrm{buy}}=\lceil N\rceil  && \text{a buy never rounds down} \\
& C_{\mathrm{sell}}=\lfloor N\rfloor  && \text{a sale never rounds up} \\
& K_{\mathrm{after}}=K_{\mathrm{before}}-C_{\mathrm{buy}}+C_{\mathrm{sell}} \\
& W_{\mathrm{after}}=W_{\mathrm{before}} && \text{stock trades never touch the wallet}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $s_{\mu }$ | Shares in micro-units (`shares_micros`) |  |
| $p_{\mu }$ | Execution price in micro-units (`execution_price_micros`) |  |
| $N$ | Exact notional (`notional_cents_exact`) | ¢ |
| $C_{\mathrm{buy}}, C_{\mathrm{sell}}$ | Purchase cost / sale proceeds | ¢ |
| $K$ | Paper-account cash (`paper_account_cash`) | Starts at \$1,000 |
| $W$ | Game wallet | ¢ |

### F11. Daily AI Coach question cap

*MVP · Owner: Ethan*

$$
\begin{aligned}
& \mathrm{allow} \iff  q_{\mathrm{used}}<Q_{\mathrm{cap}}
\end{aligned}
$$

If allowed, the question goes ahead (subject to moderation and provider availability); otherwise the daily-cap state is shown.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $q_{\mathrm{used}}$ | Questions used today (`questions_used_today`) | Resets 00:00 UTC |
| $Q_{\mathrm{cap}}$ | Daily plan cap (`daily_plan_cap`) | Free 10; Premium 30 |

### F12. Seeded demand-to-units conversion

*MVP · Owner: Ethan*

$$
\begin{aligned}
& \mathrm{type}_{i}=\mathrm{Bargain} && \text{if }u_{i}^{\mathrm{type}}<0.40 \\
& \mathrm{type}_{i}=\mathrm{Loyal} && \text{if }0.40\le u_{i}^{\mathrm{type}}<0.80 \\
& \mathrm{type}_{i}=\mathrm{Premium} && \text{if }u_{i}^{\mathrm{type}}\ge 0.80 \\
& a_{i}=A[\mathrm{min}(\lfloor u_{i}^{\mathrm{pick}}\times n_{A}\rfloor , n_{A}-1)] \\
& x_{i}=1 && \text{if }u_{i}^{\mathrm{buy}}<P_{\mathrm{buy},i}\text{ (from F26), otherwise }x_{i}=0 \\
& D=\sum_{i=0}^{V-1}{x_{i}} \\
& q=\mathrm{min}(D, Q_{\mathrm{inv}}) && \text{inventory business} \\
& q=\mathrm{min}(D, J_{\mathrm{rem}}) && \text{service business}
\end{aligned}
$$

Businesses are processed by UUID ascending and visitors by index ascending; candidate agent indexes are sorted with no shuffle.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $i$ | Visitor index (`visitor_index`) | 0 … V−1 |
| $V$ | Visitors per day (`visitors_per_day`) | Per business, Appendix A.2 |
| $u_{i}^{\mathrm{type}}, u_{i}^{\mathrm{pick}}, u_{i}^{\mathrm{buy}}$ | Seeded draws (`u_type`, `u_pick`, `u_buy`) | [0, 1) |
| $A, n_{A}$ | Sorted candidate agents (`candidates`) and their count (`len(candidates)`) |  |
| $x_{i}$ | Purchase intent (`purchase_intent`) | 0 or 1 |
| $D$ | Demand (`demand`) | units |
| $Q_{\mathrm{inv}}$ | Inventory available (`inventory_available`) | units |
| $J_{\mathrm{rem}}$ | Jobs remaining today (`jobs_remaining_today`) | jobs |
| $q$ | Units or jobs sold |  |

### F13. Gross business revenue

*MVP · Owner: Ethan*

$$
\begin{aligned}
& R_{c}=p\times q_{c} \\
& R=\sum_{c}{R_{c}}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $p$ | Selling price per unit (`selling_price_per_unit`) | \$ |
| $q_{c}$ | Units/jobs sold to customer type c |  |
| $R_{c}$ | Revenue by customer type (`revenue_by_customer_type`) | \$ |
| $R$ | Gross business revenue (`gross_business_revenue`) | \$ |

### F14. Business sales tax posting

*MVP · Owner: Ethan*

$$
\begin{aligned}
& T_{b}=\mathrm{round}(0.07\times R_{b}) && \text{for each business b in ascending UUID order; one entry per turn when }T_{b}>0
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $R_{b}$ | Taxable gross sales of business b (`taxable_gross_sales`) | ¢ |
| $T_{b}$ | Sales tax expense (`sales_tax_expense`) | ¢ |

### F15. Supply costs, operating costs, cost of goods sold, and business profit

*MVP · Owner: Ethan*

$$
\begin{aligned}
& c_{0}=\mathrm{cents}(p_{\mathrm{def}}\times \rho ) \\
& c_{m}=\mathrm{round}(c_{m-1}\times (1+\pi _{m})) \\
& X=n\times c \\
& D_{\mathrm{restock}}=\mathrm{round}(X\times (1-\delta )\times \varphi ) \\
& \varphi =0.90 && \text{if Supplier Discount fired this turn, otherwise }\varphi =1.00 \\
& \mathrm{COGS}=\sum_{\ell }{q_{\ell }\times c_{\ell }} && \text{oldest lots consumed first (FIFO)} \\
& F_{b}^{\mathrm{plat}}=\mathrm{round}(0.08\times R_{b}^{\mathrm{online}}) && \text{one entry per business per turn} \\
& B^{\mathrm{phys}}=1800\text{¢} && \text{per active physical business on turns 30, 60, 90, …} \\
& E^{\mathrm{emp}}=0 \\
& \Pi =R-T-\mathrm{COGS}-F^{\mathrm{plat}}-B^{\mathrm{phys}}-E^{\mathrm{emp}}
\end{aligned}
$$

The wallet is debited when a starter or restock order is bought.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $p_{\mathrm{def}}$ | Default template price (`default_template_price`) | \$ |
| $\rho$ | Base-type cost ratio (`base_type_cost_ratio`) |  |
| $c_{m}$ | Unit cost in month m (`inflation_adjusted_unit_cost`) | ¢/unit |
| $\pi _{m}$ | Newly observed monthly CPI change | fraction |
| $n$ | Units ordered (`units_ordered`) | units |
| $X$ | Restock order subtotal | ¢ |
| $\delta$ | Eligible bulk discount | 0 below 25; 5% for 25–99; 10% for 100+ |
| $\varphi$ | Supplier event factor | 0.90 or 1.00 |
| $D_{\mathrm{restock}}$ | Restock cash debit | ¢ |
| $q_{\ell }, c_{\ell }$ | Units sold from lot ℓ and that lot's unit cost |  |
| $F_{b}^{\mathrm{plat}}$ | Online platform fee | 8% of online sales |
| $B^{\mathrm{phys}}$ | Physical monthly bill | 1800¢ |
| $E^{\mathrm{emp}}$ | Employee cost | 0 in MVP |
| $\Pi$ | Business contribution (`business_contribution`) | ¢ |

### F16. Break-even units and contribution margin

*Stretch · Owner: Ethan*

$$
\begin{aligned}
& m_{u}=p-v-t_{u} \\
& Q_{\mathrm{BE}}=\lceil \frac{F_{\mathrm{fix}}}{m_{u}}\rceil  && \text{if }m_{u}>0 \\
& Q_{\mathrm{BE}}=\infty  && \text{if }m_{u}\le 0\text{ (no break-even at this price)}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $p$ | Selling price per unit | \$ |
| $v$ | Variable cost per unit | \$ |
| $t_{u}$ | Sales tax per unit | \$ |
| $m_{u}$ | Unit contribution (`unit_contribution`) | \$ |
| $F_{\mathrm{fix}}$ | Fixed costs (`fixed_costs`) | \$ |
| $Q_{\mathrm{BE}}$ | Break-even units (`break_even_units`) | units |

### F17. Paper-trading portfolio valuation

*MVP · Owner: Ethan*

$$
\begin{aligned}
& V_{h}=S_{h}\times P_{h} \\
& V_{H}=\sum_{h}{V_{h}} \\
& V_{\mathrm{paper}}=K+V_{H} \\
& W=W && \text{wallet value is a separate account}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $S_{h}$ | Fractional shares | shares |
| $P_{h}$ | Latest valid simulated price | \$/share |
| $V_{H}$ | Holdings value (`portfolio_holdings_value`) | \$ |
| $K$ | Paper cash (`paper_cash`) | \$ |
| $V_{\mathrm{paper}}$ | Paper portfolio value (`paper_portfolio_value`) | \$ |

### F18. Learn reward paid once per lesson

*MVP · Owner: Kevin*

$$
\begin{aligned}
& \Delta \mathrm{Pts}=10, g\leftarrow 1 && \text{if quiz passed and }g=0\text{ (granted atomically)} \\
& \Delta \mathrm{Pts}=0 && \text{otherwise (no duplicate reward)}
\end{aligned}
$$

Badges unlock when Appendix A.7 criteria are met.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $\Delta \mathrm{Pts}$ | Points granted for the lesson | 10 |
| $g$ | Reward already granted flag | 0 or 1 |

### F19. AI Coach cost reservation and monthly budget

*MVP · Owner: Ethan*

$$
\begin{aligned}
& \hat{C}=n_{\mathrm{in}}\times r_{\mathrm{in}}+n_{\mathrm{out}}\times r_{\mathrm{out}} \\
& B_{\mathrm{avail}}=20.00-C_{\mathrm{actual}}-C_{\mathrm{pend}} \\
& \mathrm{call} \iff  \mathrm{cap} \mathrm{ok} \land  \mathrm{pricing} \mathrm{current} \land  \hat{C}\le B_{\mathrm{avail}}
\end{aligned}
$$

If allowed, reserve $\hat{C}$ atomically, call the provider, then reconcile to actual cost. Otherwise reject and show the limit/unavailable state.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $\hat{C}$ | Estimated request cost (`estimated_request_cost`) | \$ |
| $n_{\mathrm{in}}, n_{\mathrm{out}}$ | Estimated input / reserved output tokens | tokens |
| $r_{\mathrm{in}}, r_{\mathrm{out}}$ | Input / output token rates | \$/token |
| $C_{\mathrm{actual}}, C_{\mathrm{pend}}$ | Month actual cost / pending reservations | \$ |
| $B_{\mathrm{avail}}$ | Available budget (`available_budget`) | Cap B_AI = \$20/month |

### F20. Month-end Money Report aggregates

*MVP · Owner: Ethan*

$$
\begin{aligned}
& \Delta W=W_{\mathrm{close}}-W_{\mathrm{open}} \\
& C_{\mathrm{debt}}=\sum{I_{\mathrm{loan}}}+\sum{I_{\mathrm{debt}}}+\sum{F_{\mathrm{OD}}} \\
& \Pi _{b}=R_{b}-T_{b}-\mathrm{COGS}_{b}-F_{b}^{\mathrm{plat}}-B_{b}^{\mathrm{rent}}-E_{b}^{\mathrm{emp}} \\
& \mathrm{top}=\mathrm{argmax}_{b} \Pi _{b} \\
& \mathrm{drain}=\mathrm{argmax}_{k} D_{k}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $W_{\mathrm{open}}, W_{\mathrm{close}}$ | Opening / closing wallet | ¢ |
| $C_{\mathrm{debt}}$ | Cost of debt (`cost_of_debt`) | ¢ |
| $I_{\mathrm{loan}}, I_{\mathrm{debt}}, F_{\mathrm{OD}}$ | Loan interest, debt interest, overdraft fees | ¢ |
| $\Pi _{b}$ | Business contribution | ¢ |
| $B_{b}^{\mathrm{rent}}$ | Rent and utilities | ¢ |
| $D_{k}$ | Actual wallet debits in expense category k | ¢ |

### F21. Spendly Premium MVP mock price

*MVP · Owner: Kevin*

$$
\begin{aligned}
& P_{\mathrm{prem}}=\$10.00/\mathrm{month} \\
& C_{\mathrm{MVP}}=\$0.00 && \text{simulated entitlement; no payment processor is called}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $P_{\mathrm{prem}}$ | Premium display price | \$10.00/month |
| $C_{\mathrm{MVP}}$ | Actual charge in MVP | \$0.00 |

### F22. One-time Lesson 0 starting-cash grant

*MVP · Owner: Ethan*

$$
\begin{aligned}
& G=+\$100, g_{0}\leftarrow 1 && \text{if Lesson 0 completed and }g_{0}=0\text{ (one transaction, tag }\texttt{starting\_cash}\text{)} \\
& G=0 && \text{otherwise}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $G$ | Starting-cash credit to the wallet | \$100 |
| $g_{0}$ | Grant already posted flag | 0 or 1 |

### F23. Loan amortization, monthly payment, and early payoff

*MVP · Owner: Ethan*

$$
\begin{aligned}
& i=\frac{\mathrm{APR}}{12} \\
& A=\mathrm{round}(\frac{P\times i}{1-{(1+i)}^{-n}}) \\
& I_{k}=\mathrm{round}(P_{k}\times i) \\
& A-I_{k} && \text{principal component} \\
& P_{k+1}=P_{k}-(A-I_{k}) \\
& A_{\mathrm{final}}=P_{k}+I_{k} && \text{last installment}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $\mathrm{APR}$ | Annual percentage rate | Appendix A.3 |
| $i$ | Monthly rate (`monthly_rate`) |  |
| $P$ | Original principal | ¢ |
| $n$ | Term in months (`term_months`) | months |
| $A$ | Scheduled payment (`scheduled_payment`) | ¢ |
| $P_{k}$ | Opening principal in month k | ¢ |
| $I_{k}$ | Monthly interest | ¢ |

### F24. Savings-jar interest and maturity

*MVP · Owner: Ethan*

$$
\begin{aligned}
& I=\mathrm{round}(J_{0}\times \frac{\mathrm{APR}}{12}) \\
& J_{\mathrm{close}}=J_{\mathrm{close}}^{\prime }+I \\
& t_{\mathrm{mat}}=t_{\mathrm{dep}}+90 \\
& V_{\mathrm{lot}}=P_{\mathrm{rem}}+I_{\mathrm{rem}} \\
& \mathrm{withdraw} \iff  (\mathrm{type}=\mathrm{basic})\lor (w\le \sum{V_{\mathrm{matured}}})
\end{aligned}
$$

Locked withdrawals use matured lots only, consuming principal then interest, FIFO.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $J_{0}$ | Jar balance at start of 30-turn period | ¢ |
| $I$ | Monthly interest | ¢ |
| $J_{\mathrm{close}}^{\prime }, J_{\mathrm{close}}$ | Closing balance before / after interest | ¢ |
| $t_{\mathrm{dep}}, t_{\mathrm{mat}}$ | Deposit turn / locked maturity turn | turn |
| $P_{\mathrm{rem}}, I_{\mathrm{rem}}$ | Remaining principal / interest in a lot | ¢ |
| $w$ | Requested withdrawal (`requested_amount`) | ¢ |

### F25. Persistent shopper pool and deterministic visitor assignment

*MVP · Owner: Ethan*

$$
\begin{aligned}
& N_{\mathrm{pool}}=100 \\
& N_{B}=40, N_{L}=40, N_{P}=20 \\
& V_{t}=\sum_{b}{v_{b}} \\
& a=A_{\mathrm{type}}[\lfloor u\times n\rfloor ] && \text{over sorted unused agents of the drawn archetype ("consumer-agent-assignment" key)} \\
& \mathrm{unique}(t, b, i), \mathrm{unique}(t, a) && \text{constraints}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $N_{\mathrm{pool}}$ | Pool size per player simulation | 100 |
| $N_{B}, N_{L}, N_{P}$ | Bargain Hunter / Loyal Regular / Premium Buyer counts | 40 / 40 / 20 |
| $v_{b}$ | Visitors per day of active business b |  |
| $V_{t}$ | Visitor opportunities in turn t |  |
| $A_{\mathrm{type}}, n$ | Unused agents of the archetype and how many there are |  |
| $a$ | Assigned agent |  |

### F26. Individual shopper purchase probability

*MVP · Owner: Ethan*

$$
\begin{aligned}
& P_{\mathrm{src}}=\mathrm{clamp}(1-{(\frac{p}{p_{\mathrm{max}}})}^{2}, 0, 1) \\
& P_{\mathrm{price}}=P_{\mathrm{src}}^{\varepsilon /1.20} \\
& M_{\mathrm{type}}=1.10 && \text{if Loyal Regular, otherwise }M_{\mathrm{type}}=1.00 \\
& M_{\mathrm{rel}}=0.90+0.20R \\
& P_{\mathrm{buy}}=\mathrm{clamp}(P_{\mathrm{price}}\times M_{\mathrm{type}}\times M_{\mathrm{rel}}, 0, 1) \\
& E[D]=\sum_{i}{P_{\mathrm{buy},i}}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $p, p_{\mathrm{max}}$ | Price and archetype maximum after scale | ¢ |
| $\varepsilon$ | Price-sensitivity exponent (`epsilon`) | [0.30, 3.00], default 1.20 |
| $R$ | Relationship score (`relationship_score`) | [0, 1], initial 0.50 |
| $M_{\mathrm{type}}, M_{\mathrm{rel}}$ | Archetype and relationship modifiers |  |
| $P_{\mathrm{src}}, P_{\mathrm{price}}, P_{\mathrm{buy}}$ | Source, individualized and final buy probability | [0, 1] |
| $E[D]$ | Expected demand (`expected_demand`) |  |

### F27. Shopper relationship and price-sensitivity learning

*MVP · Owner: Ethan*

$$
\begin{aligned}
& R^{\prime }=\mathrm{clamp}(R+0.02s, 0, 1) \\
& s=+1 && \text{fulfilled purchase} \\
& s=-1 && \text{valid intent not fulfilled because stock or service capacity ran out} \\
& s=0 && \text{ordinary price/preference rejection} \\
& M=M_{\mathrm{type}}\times M_{\mathrm{rel}} \\
& P_{\mathrm{raw}}=M\times P_{\mathrm{price}} \\
& P_{\mathrm{buy}}=\mathrm{clamp}(P_{\mathrm{raw}}, 0, 1) \\
& \frac{\partial P_{\mathrm{buy}}}{\partial \varepsilon }=M\times \frac{P_{\mathrm{price}}}{1.20}\times \ln  P_{\mathrm{src}} && \text{only when }0<P_{\mathrm{src}}<1\text{ and }0<P_{\mathrm{raw}}<1\text{; otherwise 0} \\
& \varepsilon _{\mathrm{raw}}=\varepsilon -0.05(P_{\mathrm{buy}}-y)\frac{\partial P_{\mathrm{buy}}}{\partial \varepsilon } \\
& \varepsilon _{\mathrm{step}}=\mathrm{clamp}(\varepsilon _{\mathrm{raw}}, 0.95\varepsilon , 1.05\varepsilon ) \\
& \varepsilon ^{\prime }=\mathrm{clamp}(\varepsilon _{\mathrm{step}}, 0.30, 3.00)
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $R, R^{\prime }$ | Relationship score now / next | [0, 1] |
| $s$ | Experience signal (`experience_signal`) | +1, −1 or 0 |
| $y$ | Observed purchase (`observed_buy`) | 1 bought, 0 rejected |
| $\varepsilon , \varepsilon ^{\prime }$ | Price sensitivity now / next | [0.30, 3.00] |

## 3. Simulated stock price (Appendix A.6)

Quotes update every five real-time minutes (288 ticks per day) in each player's own market world. Prices keep six decimals internally and are rounded to cents for display only.

$$
\begin{aligned}
& \pi _{\mathrm{yoy}}=(\frac{\mathrm{CPI}_{t}}{\mathrm{CPI}_{t-12}}-1)\times 100 \\
& \Delta r=\mathrm{DFF}_{t}-\mathrm{DFF}_{t-1} && \text{percentage points} \\
& \beta =\mathrm{clamp}(-0.001\Delta r-0.0005(\pi _{\mathrm{yoy}}-2.0), -0.02, 0.02) \\
& \xi \sim U[-0.0005, 0.0005] && \text{seeded from (market seed, ticker, tick timestamp), purpose "market-noise"} \\
& r_{\mathrm{tick}}=\mathrm{clamp}(\frac{\beta }{288}+\xi , -0.005, 0.005) \\
& P_{n+1}=\mathrm{max}(\$0.01, P_{n}(1+r_{\mathrm{tick}}))
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $\mathrm{CPI}_{t}$ | FRED CPIAUCSL index, month t |  |
| $\pi _{\mathrm{yoy}}$ | CPI year-over-year percent (`CPI_yoy_percent`) | % |
| $\mathrm{DFF}_{t}$ | FRED Federal Funds Effective Rate | % |
| $\Delta r$ | Change in DFF (`delta_DFF_pp`) | pp |
| $\beta$ | Macro daily bias (`macro_daily_bias`) | [−0.02, 0.02] |
| $\xi$ | Per-tick noise (`epsilon` in A.6) |  |
| $r_{\mathrm{tick}}$ | Tick return (`tick_return`) | [−0.005, 0.005] |
| $P_{n}$ | Share price after tick n | \$, floor \$0.01 |
| $288$ | Five-minute ticks per day |  |

## 4. Consumer-agent formulas M1–M16 (Appendix A.26 §5)

M2 and M4 are MVP and extend F26 and F27. The rest are Stretch, using proposed V2.8 defaults.

### M1. Product score and affordability

*Stretch*

$$
\begin{aligned}
& \mathrm{over} \mathrm{budget} && \text{if }B\le 0\text{ or }p>B\text{ (checked before dividing)} \\
& S=w_{q}q+(1-w_{q})(1-\frac{p}{B}) \\
& \mathrm{accept} \iff  S\ge \theta  \\
& \mathrm{choice}=\mathrm{argmax} S && \text{tie-break by stable product ID}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $p$ | Candidate product price | ¢ |
| $B$ | Resident daily purchase budget | ¢ |
| $q$ | Product quality rating | [0, 1] |
| $w_{q}$ | Resident quality weight (`wq`) | [0, 1], mean 0.50 |
| $\theta$ | Buy threshold (`theta`) | 0.35 |
| $S$ | Product score | [0, 1] |

### M2. Spendly demand and individual price sensitivity

*MVP*

$$
\begin{aligned}
& P_{\mathrm{src}}=\mathrm{clamp}(1-{(\frac{p}{p_{\mathrm{max}}})}^{2}, 0, 1) \\
& P_{\mathrm{price}}=P_{\mathrm{src}}^{\varepsilon /1.20} \\
& M_{\mathrm{type}}=1.10 && \text{Loyal Regular; 1.00 for other archetypes} \\
& M_{\mathrm{rel}}=0.90+0.20R \\
& P_{\mathrm{buy}}=\mathrm{clamp}(P_{\mathrm{price}}M_{\mathrm{type}}M_{\mathrm{rel}}, 0, 1) \\
& E[D]=\sum_{i}{P_{\mathrm{buy},i}}
\end{aligned}
$$

The power law $D=D_{0}{(p/p_{\mathrm{ref}})}^{-\varepsilon }$ is not used as a buying probability: it is undefined at $p=0$ and can exceed the visitor count.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $p, p_{\mathrm{max}}$ | Posted price / archetype-business maximum | ¢ |
| $\varepsilon$ | Price-sensitivity exponent | [0.30, 3.00], default 1.20 |
| $R$ | Per-business relationship | [0, 1], initial 0.50 |
| $M_{\mathrm{type}}$ | Archetype modifier | 1.00 or 1.10 |
| $M_{\mathrm{rel}}$ | Relationship multiplier | [0.90, 1.10] |

### M3. Business choice (city routing)

*Stretch*

$$
\begin{aligned}
& w_{b}=I_{b}A_{b} \\
& P(b)=\frac{w_{b}}{\sum_{j}{w_{j}}} \\
& P(\mathrm{last})=\lambda +(1-\lambda )\frac{w_{\mathrm{last}}}{\sum_{j}{w_{j}}} && \text{when the last-happy business is eligible} \\
& \mathrm{no} \mathrm{visit} && \text{if }\sum_{j}{w_{j}}=0
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $I_{b}$ | Resident interest in business b | ≥ 0, initial 1.00 |
| $A_{b}$ | Business attractiveness | ≥ 0 |
| $w_{b}$ | Business choice weight |  |
| $\lambda$ | Return-to-last-happy probability (`lambda`) | [0, 0.90], 0.25 |
| $P(b)$ | Business selection probability | [0, 1] |

### M4. Preference learning: relationship and price sensitivity

*MVP*

$$
\begin{aligned}
& R^{\prime }=\mathrm{clamp}(R+\eta _{R}s, 0, 1) \\
& M=M_{\mathrm{type}}M_{\mathrm{rel}}, P_{\mathrm{raw}}=M\times P_{\mathrm{price}}, P_{\mathrm{buy}}=\mathrm{clamp}(P_{\mathrm{raw}}, 0, 1) \\
& \frac{\partial P_{\mathrm{buy}}}{\partial \varepsilon }=M\frac{P_{\mathrm{price}}}{1.20}\ln  P_{\mathrm{src}} && \text{when }0<P_{\mathrm{src}}<1\text{ and }0<P_{\mathrm{raw}}<1\text{; otherwise 0} \\
& \varepsilon _{\mathrm{raw}}=\varepsilon -\eta _{\varepsilon }(P_{\mathrm{buy}}-y)\frac{\partial P_{\mathrm{buy}}}{\partial \varepsilon } \\
& \varepsilon ^{\prime }=\mathrm{clamp}(\mathrm{clamp}(\varepsilon _{\mathrm{raw}}, \varepsilon (1-X), \varepsilon (1+X)), 0.30, 3.00)
\end{aligned}
$$

No price-sensitivity update on closures, event suppression, stockout after intent, or service-capacity exhaustion.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $R$ | Agent/business relationship score | [0, 1], initial 0.50 |
| $s$ | Experience signal | −1, 0 or +1 |
| $\eta _{R}$ | Relationship step (`eta_R`) | 0.02 |
| $\varepsilon$ | Price sensitivity | [0.30, 3.00] |
| $\eta _{\varepsilon }$ | Gradient learning rate (`eta_epsilon`) | 0.05 |
| $X$ | Max daily relative ε movement | 0.05 |
| $y$ | Observed purchase result | 1 or 0 |

### M5. Child creation and bounded trait mutation

*Stretch*

$$
\begin{aligned}
& P_{\mathrm{spawn}}=0 && \text{if population is at or above the cap} \\
& P_{\mathrm{spawn}}=0.001\times \mathrm{min}(1, \frac{\mathrm{max}(0, F)}{10000}) && \text{otherwise} \\
& z\sim \mathrm{TN}(0, 0.05^{2}, -0.10, 0.10) \\
& w_{\mathrm{child}}=\mathrm{clamp}(w_{\mathrm{parent}}(1+z), \mathrm{lower}, \mathrm{upper}) \\
& F_{\mathrm{child}}=\mathrm{round}(0.05F_{\mathrm{parent}}) && \text{moved from parent via two balanced city-ledger entries}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $F$ | Resident available funds | ¢ |
| $10000$ | Funds reference F_ref | ¢ |
| $0.001$ | Base daily spawn chance p_base |  |
| $z$ | Trait mutation (truncated normal) | [−0.10, 0.10] |
| $w_{\mathrm{parent}}, w_{\mathrm{child}}$ | Inheritable trait of parent / child |  |

### M6. Resident funds and daily purchase budget

*Stretch*

$$
\begin{aligned}
& F_{\mathrm{avail}}=\mathrm{max}(0, F_{0}+y_{d}) \\
& B=\lfloor \mathrm{min}(F_{\mathrm{avail}}, \mathrm{max}(0, 0.20F_{0}+y_{d}))\rfloor 
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $F_{0}$ | Opening funds before today's income | ¢ |
| $y_{d}$ | Income today | ¢ |
| $F_{\mathrm{avail}}$ | Funds available today | ¢ |
| $0.20$ | Discretionary share of opening funds |  |
| $B$ | Daily budget | ¢ |

### M7. Hunger, thirst, sleep, and urgency

*Stretch*

$$
\begin{aligned}
& h^{\prime }=\mathrm{clamp}(\mathrm{min}(1, h+0.04\tau _{a})-0.55e_{f}, 0, 1) \\
& t^{\prime }=\mathrm{clamp}(\mathrm{min}(1, t+0.06\tau _{a})-0.65e_{d}, 0, 1) \\
& s^{\prime }=\mathrm{clamp}(\mathrm{min}(1, s+0.05\tau _{a})-0.15\tau _{s}Q_{h}, 0, 1) \\
& U(n, g)=\mathrm{clamp}(\frac{n-g}{1-g}, 0, 1) && \text{for need n and trigger }g<1
\end{aligned}
$$

Highest positive urgency goes first; ties resolve thirst, hunger, sleep, then discretionary choice.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $h, t, s$ | Hunger, thirst, sleep need | [0, 1] |
| $\tau _{a}, \tau _{s}$ | Hours awake / hours slept | hours/day |
| $e_{f}, e_{d}$ | Ate / drank this period | 0 or 1 |
| $Q_{h}$ | Home sleep quality | [0, 1] |
| $g$ | Need priority trigger | thirst .45, hunger .55, sleep .65 |
| $U$ | Urgency | [0, 1] |

### M8. Mood and derived behavior modifiers

*Stretch*

$$
\begin{aligned}
& m^{*}=\sum_{k}{a_{k}x_{k}} \\
& m^{\prime }=\mathrm{clamp}(m+0.05(m^{*}-m), 0, 1) \\
& \lambda _{\mathrm{eff}}=\mathrm{clamp}(\lambda (0.8+0.4m), 0, 0.90) \\
& \varepsilon _{\mathrm{eff}}=\mathrm{clamp}(\varepsilon (1.2-0.4m), 0.30, 3.00)
\end{aligned}
$$

Drivers $x_{k}$: funds ratio, job status, $1-h$, $1-t$, $1-s$, health, craving met, home quality. Weights $a_{k}$ sum to 1.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $x_{k}$ | Normalized mood driver | [0, 1] |
| $a_{k}$ | Driver weight | [0, 1] |
| $m, m^{*}$ | Prior mood / weighted mood target | [0, 1] |
| $0.05$ | Smoothing factor α |  |
| $\lambda _{\mathrm{eff}}, \varepsilon _{\mathrm{eff}}$ | Effective return loyalty / price sensitivity |  |

### M9. Age hazard and departure

*Stretch*

$$
\begin{aligned}
& H=\mathrm{min}(20, h_{0}e^{k(\mathrm{age}-a_{0})}) \\
& P_{\mathrm{depart}}=1-e^{-H\Delta d}
\end{aligned}
$$

At the max-age limit the resident is marked retired regardless of the draw.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $\mathrm{age}$ | Fictional resident age |  |
| $h_{0}$ | Base daily departure hazard |  |
| $k$ | Hazard growth coefficient |  |
| $a_{0}$ | Reference age |  |
| $H$ | Capped hazard | ≤ 20 |
| $\Delta d$ | Elapsed simulation days (`DeltaDays`) | days |

### M10. Housing affordability and move choice

*Stretch*

$$
\begin{aligned}
& a=\frac{\mathrm{rent}}{\mathrm{income}} && \text{if income > 0} \\
& a=+\infty  && \text{if income = 0 and rent > 0} \\
& a=0 && \text{if both are 0} \\
& P_{\mathrm{move}}=\mathrm{clamp}(0.05+0.50max(0, a-0.50), 0.05, 0.50) && \text{after }a>0.50\text{ for 7 consecutive days} \\
& a\le 0.35 && \text{target affordability}
\end{aligned}
$$

Rent is due every 30 days with a 7-day grace period and one 200¢ late fee per unpaid cycle.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $\mathrm{rent}, \mathrm{income}$ | Monthly rent / income | ¢ |
| $a$ | Rent-to-income affordability ratio |  |
| $P_{\mathrm{move}}$ | Move probability after the trigger | [0.05, 0.50] |

### M11. Job negotiation

*Stretch*

$$
\begin{aligned}
& M=\mathrm{clamp}(M_{0}(1-0.20P+0.15S), w_{\mathrm{min}}, w_{\mathrm{max}}) \\
& w_{\mathrm{ask}}=\mathrm{clamp}(1.10M_{0}, w_{\mathrm{min}}, w_{\mathrm{max}}) \\
& P_{\mathrm{accept}}=1 && \text{if }O\ge M \\
& P_{\mathrm{accept}}=1-\frac{M-O}{0.10M} && \text{if }0.90M\le O<M \\
& P_{\mathrm{accept}}=0 && \text{otherwise} \\
& \mathrm{accept} \iff  u<P_{\mathrm{accept}}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $M_{0}$ | Expected role wage from posting | ¢/hour |
| $P$ | Normalized financial/need pressure | [0, 1] |
| $S$ | Normalized resident strength | [0, 1] |
| $0.20, 0.15$ | Pressure κ / strength μ coefficients |  |
| $M$ | Walk-away minimum | ¢/hour |
| $O$ | Employer wage offer | ¢/hour |
| $w_{\mathrm{min}}, w_{\mathrm{max}}$ | Posting wage limits |  |

### M12. Age-linked resident behavior

*Stretch*

$$
\begin{aligned}
& A=\mathrm{clamp}(\frac{d_{\mathrm{age}}}{3650}, 0, 1) \\
& F_{0}=\mathrm{round}(10000(0.75+0.50A)) \\
& \varepsilon _{\mathrm{age}}=\mathrm{clamp}(\varepsilon (1.20-0.40A), 0.30, 3.00) \\
& \lambda _{\mathrm{age}}=\mathrm{clamp}(0.25(0.75+0.50A), 0, 0.90) \\
& \sigma _{d}=0.20-0.10A
\end{aligned}
$$

Mood factors from M8 apply afterwards.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $d_{\mathrm{age}}$ | Age in days (`age_days`) | days |
| $A$ | Normalized age | [0, 1] |
| $F_{0}$ | Initial funds (`initial_funds`) | ¢ |
| $\sigma _{d}$ | Daily spending share (`daily_share`) |  |

### M13. Craving generation and meal-time demand

*Stretch*

$$
\begin{aligned}
& \mathrm{craving} \mathrm{starts} && \text{if none is active and }u<p_{\mathrm{crave}}\text{; lasts 3 days} \\
& I_{\mathrm{match}}^{\prime }=1.20I_{\mathrm{match}} \\
& \varepsilon ^{\prime }=\mathrm{clamp}(0.95\varepsilon , 0.30, 3.00) \\
& \mu _{\mathrm{food}}=1.15 && \text{07:00–09:59} \\
& \mu _{\mathrm{food}}=1.25 && \text{11:00–14:59} \\
& \mu _{\mathrm{food}}=1.20 && \text{17:00–20:59; otherwise 1.00} \\
& \mu _{\mathrm{drink}}=1.15 && \text{10:00–19:59; otherwise 1.00} \\
& \mu _{\mathrm{weather}}=1.10 && \text{drinks during the Good Weather event} \\
& \mathrm{priority}=U\times \mu _{\mathrm{time}}\times \mu _{\mathrm{weather}}
\end{aligned}
$$

Priority affects choice order only and never bypasses available funds.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $p_{\mathrm{crave}}$ | Craving chance |  |
| $I_{\mathrm{match}}$ | Interest in the craved product kind |  |
| $\mu$ | Time-of-day or weather multiplier |  |
| $U$ | Urgency from M7 |  |

### M14. Job search and work reliability

*Stretch*

$$
\begin{aligned}
& J=0.40f_{w}+0.30f_{h}+0.30f_{k} \\
& \rho _{w}=\mathrm{clamp}(1-0.20s-0.15h-0.20t-0.15(1-H)+0.10(m-0.50), 0, 1) \\
& k_{\mathrm{eff}}=\mathrm{clamp}(k_{0}(0.90+0.20A)\rho _{w}, 0, 1) \\
& J_{\mathrm{morale}}=0.40\sigma _{w}+0.30f_{h}+0.30m \\
& \mathrm{Pay}=\mathrm{round}(c_{h}(\mathrm{min}(n, 40)+1.50max(0, n-40))) && \text{hours }n\le 60
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $f_{w}, f_{h}, f_{k}$ | Wage, hours and skill fit | [0, 1] |
| $s, h, t$ | Sleep need, hunger, thirst | [0, 1] |
| $H$ | Health | [0, 1] |
| $m$ | Mood | [0, 1] |
| $\rho _{w}$ | Work reliability | [0, 1] |
| $k_{0}, k_{\mathrm{eff}}$ | Base / effective skill | [0, 1] |
| $\sigma _{w}$ | Wage satisfaction | [0, 1] |
| $c_{h}$ | Hourly wage | ¢ |
| $n$ | Weekly hours | ≤ 60 |

### M15. Departure and city-ledger transfer

*Stretch*

$$
\begin{aligned}
& \delta =1 && \text{if }F=0\text{ or }h\ge 0.95\text{ or }t\ge 0.95\text{ or }H\le 0.10\text{; otherwise }\delta =0 \\
& d^{\prime }=d+1 && \text{if }\delta =1\text{; otherwise }d^{\prime }=0 \\
& \mathrm{moves} \mathrm{away} && \text{when }d=7
\end{aligned}
$$

On departure or retirement the remaining funds move to `CITY_RESERVE` in one unique-key transaction.

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $\delta$ | Deprived today | 0 or 1 |
| $F$ | Funds | ¢ |
| $h, t, H$ | Hunger, thirst, health | [0, 1] |
| $d$ | Consecutive deprivation days | days |

### M16. Injury and recovery state

*Stretch*

$$
\begin{aligned}
& H^{\prime }=\mathrm{clamp}(H-0.10, 0, 1) && \text{on a seeded daily injury draw }u<0.005\text{; work hours ×0.5 that day} \\
& C_{\mathrm{treat}}=200\text{¢} && \text{if treatment is chosen and funds ≥ 200¢; otherwise 0} \\
& H^{\prime }=\mathrm{clamp}(H+0.20, 0, 1) && \text{on a rest day}
\end{aligned}
$$

**Where**

| Symbol | Meaning (spec name) | Value / unit |
|---|---|---|
| $H$ | Health | [0, 1] |
| $C_{\mathrm{treat}}$ | Treatment debit | 200¢ |
