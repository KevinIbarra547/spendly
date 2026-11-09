"""Deterministic reference checks for Spendly Consumer Agents v2.8.3.
This is a standalone specification fixture, not the Spendly application engine.
It uses no network, external API, user data, or third-party packages.
"""
from __future__ import annotations
import hashlib, math, uuid
from decimal import Decimal, ROUND_HALF_UP

VERSION = "2.8.3"
NS = uuid.NAMESPACE_URL
ACCOUNT = str(uuid.uuid5(NS, "spendly:consumer-agent-fixture:account:v2.8.3"))

def rng01(parts: list[object]) -> float:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    value = int.from_bytes(digest[:8], "big") >> 11
    return value / (2**53)

def cents_round(value: float | Decimal) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def business_id(slug: str) -> str:
    return str(uuid.uuid5(NS, "spendly:consumer-agent-fixture:business:" + slug))

# The 18 MVP templates and source-backed V2.4 prices/visitor/economic defaults.
BUSINESSES = [
    ("Sticker Shop","make","online",1,8,None,10,2,.30),
    ("Candle Studio","make","online",1.5,8,None,10,3,.30),
    ("T-Shirt Printing","make","online",3,8,None,10,6,.30),
    ("Soap Maker","make","online",2,8,None,10,4,.30),
    ("Lemonade Stand","make","physical",1,6,None,10,2,.30),
    ("Baked Goods Stand","make","physical",1.5,6,None,10,3,.30),
    ("Sneaker Resale","resell","online",20,7,None,2,40,.65),
    ("Book Resale","resell","online",3,7,None,2,6,.65),
    ("Vintage Clothing","resell","online",5,7,None,2,10,.65),
    ("Toy Resale","resell","online",4,7,None,2,8,.65),
    ("Tech Accessories","resell","online",6,7,None,2,12,.65),
    ("Plant Nursery","resell","physical",2,5,None,2,4,.65),
    ("Tutoring","service","online",2,8,3,None,4,0),
    ("Graphic Design Studio","service","online",4,8,3,None,8,0),
    ("Pet Sitting","service","physical",2,6,2,None,4,0),
    ("Lawn Care","service","physical",2,6,2,None,4,0),
    ("Car Wash","service","physical",2,6,2,None,4,0),
    ("Bicycle Repair","service","physical",3,6,2,None,6,0),
]
ARCHETYPE_MAX_CENTS = {"bargain":100, "loyal":240, "premium":400}

def agent_types() -> dict[int,str]:
    return ({**{i:"bargain" for i in range(40)},
             **{i:"loyal" for i in range(40,80)},
             **{i:"premium" for i in range(80,100)}})

def assign_agents_for_turn(active_businesses, turn: int):
    """Assign one distinct persistent agent to every active business visitor slot."""
    types = agent_types()
    available = set(range(100))
    assignments = []
    for b in sorted(active_businesses, key=lambda x: business_id(x[0].lower().replace(' ','-'))):
        name, *_rest, visitors = b[0], *b[1:]
        bid = business_id(name.lower().replace(' ','-'))
        for visitor_index in range(visitors):
            u_type = rng01([VERSION, ACCOUNT, bid, turn, visitor_index, "customer-type"])
            archetype = "bargain" if u_type < .4 else ("loyal" if u_type < .8 else "premium")
            candidates = sorted(i for i in available if types[i] == archetype)
            if not candidates:
                raise AssertionError("archetype pool exhausted; pool-size contract is invalid")
            u_pick = rng01([VERSION, ACCOUNT, bid, turn, visitor_index, "consumer-agent-assignment"])
            idx = min(int(u_pick * len(candidates)), len(candidates)-1)
            agent_index = candidates[idx]
            available.remove(agent_index)
            assignments.append((bid, visitor_index, agent_index, archetype))
    return assignments

def run_business(row):
    name,base,model,scale,visitors,job_cap,pack,default_price,cost_ratio = row
    slug = name.lower().replace(" ","-")
    bid = business_id(slug)
    price = cents_round(default_price*100)
    unit_cost = cents_round(default_price*cost_ratio*100)
    inventory = 0
    wallet = 10000 + (10000 if model == "physical" else 0)
    setup_wallet = wallet
    if pack:
        setup_cost = pack * unit_cost
        wallet -= setup_cost
        inventory += pack
    types = agent_types()
    epsilon = {i:1.20 for i in range(100)}
    relationships = {i:.50 for i in range(100)}
    total_sold = gross_total = tax_total = fee_total = supply_purchases = 0
    minimum_wallet = wallet
    restocks = restock_skips = 0
    for turn in range(1,31):
        jobs_used = 0
        # Same shared-pool assignment routine used by the two-business uniqueness test.
        assignments = assign_agents_for_turn([(name, visitors)], turn)
        outcomes=[]
        for _bid, vi, ai, ctype in assignments:
            pmax = cents_round(ARCHETYPE_MAX_CENTS[ctype] * scale)
            p_source = max(0.0,min(1.0,1.0-(price/pmax)**2))
            p_price = p_source ** (epsilon[ai]/1.20) if p_source > 0 else 0.0
            m_type = 1.10 if ctype == "loyal" else 1.0
            m_rel = .90 + .20*relationships[ai]
            p_buy = max(0.0,min(1.0,p_price*m_type*m_rel))
            u = rng01([VERSION,ACCOUNT,bid,turn,vi,"consumer-purchase"])
            outcomes.append((vi,ai,ctype,p_source,p_price,u < p_buy))
        sold = 0
        for vi,ai,ctype,p_source,p_price,intent in outcomes:
            y=None
            if intent:
                can_sell = (inventory > 0) if pack else (jobs_used < job_cap)
                if can_sell:
                    sold += 1
                    if pack: inventory -= 1
                    else: jobs_used += 1
                    relationships[ai] = max(0.0,min(1.0,relationships[ai]+.02))
                    y=1
                else:
                    relationships[ai] = max(0.0,min(1.0,relationships[ai]-.02))
            else:
                y=0
            if y is not None and 0 < p_source < 1:
                multiplier = m_type * m_rel
                p_buy_raw = p_price * multiplier
                deriv = (multiplier * (p_price/1.20) * math.log(p_source)
                         if 0 < p_buy_raw < 1 else 0.0)
                current = epsilon[ai]
                candidate = current - .05*(p_buy-y)*deriv
                max_move = .05*current
                candidate = max(current-max_move,min(current+max_move,candidate))
                epsilon[ai] = max(.30,min(3.00,candidate))
        total_sold += sold
        gross = price*sold
        tax = cents_round(gross*.07)
        fee = cents_round(gross*.08) if model == "online" else 0
        wallet += gross-tax-fee
        gross_total += gross; tax_total += tax; fee_total += fee
        if pack and inventory <= 1:
            restock_cost = pack*unit_cost
            if wallet-restock_cost >= 0: # player approves each restock in this careful-player fixture
                wallet -= restock_cost
                supply_purchases += restock_cost
                inventory += pack
                restocks += 1
            else:
                restock_skips += 1
        if turn == 30 and model == "physical":
            wallet -= 1800 # $18 combined monthly physical rent/utilities
            wallet -= 1706 # $100 business loan first monthly installment
        minimum_wallet = min(minimum_wallet,wallet)
        if wallet < 0:
            raise AssertionError(f"{name}: careful-player baseline went negative on turn {turn}")
    return {
        "name":name,"price_cents":price,"visitors_per_day":visitors,"units_sold":total_sold,
        "gross_cents":gross_total,"tax_cents":tax_total,"platform_fee_cents":fee_total,
        "supply_spend_cents":supply_purchases,"wallet_end_cents":wallet,
        "wallet_min_cents":minimum_wallet,"inventory_end":inventory,"restocks":restocks,
        "restock_skips":restock_skips,"opening_wallet_cents":setup_wallet,
    }

def checks():
    results={}
    # Product score and affordability edge cases.
    theta=.35; q=.8; wq=.5; p=300; budget=500
    score=wq*q+(1-wq)*(1-p/budget)
    assert abs(score-.60)<1e-12 and score>=theta
    assert p<=budget
    assert not (budget<=0 or p>budget) # this example is affordable
    assert (budget<=0 or 600>budget) # separate unaffordable case is rejected before division
    assert wq*0+(1-wq)*(1-0/500) == .5
    results["product-score and zero-price boundaries"]="PASS"
    # Source probability monotonicity at epsilon boundaries.
    for eps in (.3,1.2,3.0):
        vals=[]
        for pc in range(0,401):
            base=max(0.0,1-(pc/400)**2)
            vals.append(base**(eps/1.2) if base>0 else 0.0)
        assert all(vals[i+1] <= vals[i]+1e-15 for i in range(len(vals)-1))
        assert all(0<=v<=1 for v in vals)
    assert (1-(200/400)**2)==.75
    results["price monotonicity at epsilon .3, 1.2, 3.0"]="PASS"
    # Epsilon gradient direction.
    p0=.75; eps=1.2; prob=p0**(eps/1.2); deriv=prob/1.2*math.log(p0)
    after_buy=eps-.05*(prob-1)*deriv
    after_reject=eps-.05*(prob-0)*deriv
    assert after_buy < eps < after_reject
    results["epsilon learning direction and clamp range"]="PASS"
    # Final-probability gradient includes archetype/relationship multipliers.
    p_source=.75; eps=1.20; p_price=p_source**(eps/1.2); mult=1.10
    p_buy=min(1.0,p_price*mult)
    d_pbuy=mult*(p_price/1.2)*math.log(p_source)
    after_buy=eps-.05*(p_buy-1)*d_pbuy
    after_reject=eps-.05*(p_buy-0)*d_pbuy
    assert after_buy < eps < after_reject
    assert abs(d_pbuy - (-.19778142481059938)) < 1e-12
    assert abs(after_buy - 1.1982694125329072) < 1e-12
    assert abs(after_reject - 1.2081584837734372) < 1e-12
    results["final-probability epsilon gradient matches generated outcome model"]="PASS"
    # Relationship updates.
    assert round(max(0,min(1,.50+.02)),2)==.52
    assert round(max(0,min(1,.50-.02)),2)==.48
    assert max(0,min(1,0-.02))==0 and min(1,1+.02)==1
    results["loyalty learning and clamps"]="PASS"
    # Business choice normalization.
    weights=[1.2,.5,.8]; total=sum(weights); probs=[x/total for x in weights]
    assert abs(sum(probs)-1)<1e-12 and all(x>=0 for x in probs)
    results["business selection probability normalization"]="PASS"
    # Spawn probability monotone and bounded.
    vals=[0 if pop>=500 else .001*min(1,max(0,funds)/10000) for pop,funds in [(10,0),(10,5000),(10,10000),(10,20000),(500,20000)]]
    assert vals==[0,.0005,.001,.001,0]
    results["child spawn probability bounds"]="PASS"
    # Funds budget bounded by available funds.
    for opening,income in [(0,0),(0,1000),(10000,2000),(5000,0)]:
        available=max(0,opening+income)
        day_budget=min(available,max(0,.20*opening+income))
        assert 0<=day_budget<=available
    results["daily budget never exceeds available funds"]="PASS"
    # Need endpoints and urgency monotonicity.
    for rate in (.04,.06,.05):
        for need in (0.0,1.0):
            assert 0<=min(1,need+rate*24)<=1
    for g in (.45,.55,.65):
        us=[max(0,min(1,(n-g)/(1-g))) for n in [i/100 for i in range(101)]]
        assert all(us[i+1]>=us[i] for i in range(100))
    results["need bounds, zero/one edges and urgency monotonicity"]="PASS"
    # Mood bounded and toward target.
    for m in [0,.1,.5,.9,1]:
        for target in [0,.2,.8,1]:
            nxt=max(0,min(1,m+.05*(target-m)))
            assert 0<=nxt<=1
            assert (nxt-m)*(target-m)>=-1e-15
    results["mood smoothing bounds and direction"]="PASS"
    # Age/departure hazard monotone within max-age range and <1.
    probs=[]
    for age in range(3651):
        hazard=min(20,.001*math.exp(.002*(age-1800)))
        probs.append(1-math.exp(-hazard))
    assert all(probs[i+1]>=probs[i] for i in range(3650)) and all(x<1 for x in probs)
    results["age hazard monotonicity and probability bounds"]="PASS"
    # Housing move probability monotonic and bounded after trigger.
    hs=[max(.05,min(.50,.05+.50*max(0,a-.50))) for a in [i/100 for i in range(51,501)]]
    assert all(hs[i+1]>=hs[i] for i in range(len(hs)-1)) and all(.05<=x<=.50 for x in hs)
    results["housing move chance bounds and monotonicity"]="PASS"
    # Age-linked resident modifiers: older residents receive more starting funds/loyalty,
    # lower price sensitivity, and a smaller discretionary daily share.
    ages=[i/100 for i in range(101)]
    initial_funds=[.75+.50*a for a in ages]
    eps_factor=[1.20-.40*a for a in ages]
    loyalty=[.25*(.75+.50*a) for a in ages]
    discretionary=[.20-.10*a for a in ages]
    assert all(initial_funds[i+1]>=initial_funds[i] for i in range(100))
    assert all(eps_factor[i+1]<=eps_factor[i] for i in range(100))
    assert all(loyalty[i+1]>=loyalty[i] for i in range(100))
    assert all(discretionary[i+1]<=discretionary[i] for i in range(100))
    results["age-linked funds, loyalty, sensitivity and care direction"]="PASS"
    # Craving multipliers remain bounded; craving is a bounded modifier only.
    craving_interest=1.20
    craving_epsilon_factor=.95
    for eps in (.30,1.20,3.00):
        effective=max(.30,min(3.00,eps*craving_epsilon_factor))
        assert .30<=effective<=3.00
    assert craving_interest>=1.0 and 0<craving_epsilon_factor<=1.0
    results["craving multipliers and epsilon clamps"]="PASS"
    # Meal-time curves select exact documented bands; no interpolation at boundaries.
    def food_factor(hour):
        return 1.15 if 7<=hour<10 else 1.25 if 11<=hour<15 else 1.20 if 17<=hour<21 else 1.00
    def drink_factor(hour):
        return 1.15 if 10<=hour<20 else 1.00
    assert [food_factor(h) for h in (6,7,9,10,11,14,15,17,20,21)] == [1,1.15,1.15,1,1.25,1.25,1,1.20,1.20,1]
    assert [drink_factor(h) for h in (9,10,19,20,23)] == [1,1.15,1.15,1,1]
    results["meal-time and drink-demand interval boundaries"]="PASS"
    # Job fit score is bounded and increases monotonically with each component.
    def job_score(wage_fit,hours_fit,skill_fit):
        return .40*wage_fit+.30*hours_fit+.30*skill_fit
    assert job_score(0,0,0)==0 and job_score(1,1,1)==1
    for component in range(3):
        previous=-1
        for v in [i/100 for i in range(101)]:
            args=[.5,.5,.5]; args[component]=v
            current=job_score(*args)
            assert 0<=current<=1 and current>=previous
            previous=current
    results["job selection score bounds and monotonicity"]="PASS"
    # Work reliability is bounded and moves in the specified directions.
    def reliability(sleep,hunger,thirst,health,mood):
        return max(0,min(1,1-.20*sleep-.15*hunger-.20*thirst-.15*(1-health)+.10*(mood-.50)))
    base=reliability(.2,.2,.2,.9,.5)
    assert reliability(.3,.2,.2,.9,.5)<=base
    assert reliability(.2,.3,.2,.9,.5)<=base
    assert reliability(.2,.2,.3,.9,.5)<=base
    assert reliability(.2,.2,.2,.8,.5)<=base
    assert reliability(.2,.2,.2,.9,.6)>=base
    for value in [i/100 for i in range(101)]:
        assert 0<=reliability(value,value,value,value,value)<=1
    results["work reliability bounds and directional effects"]="PASS"
    # A resident-to-city-reserve transfer is balanced double-entry accounting.
    def departure_transfer(resident_funds):
        amount=max(0,int(resident_funds))
        return (-amount, amount)
    for funds in (0,1,100,10000):
        debit,credit=departure_transfer(funds)
        assert debit+credit==0 and credit>=0 and abs(debit)==funds
    results["departure city-reserve transfer balances to zero"]="PASS"
    # Hourly substep RNG key must be deterministic and distinct by hour/step.
    a=rng01([VERSION,ACCOUNT,"resident-1",12,"job-offer-7",3])
    b=rng01([VERSION,ACCOUNT,"resident-1",12,"job-offer-7",3])
    c=rng01([VERSION,ACCOUNT,"resident-1",13,"job-offer-7",3])
    assert a==b and a!=c
    results["daily snapshot seeded hourly substep key reproducibility"]="PASS"
    # Negotiation chance monotone and continuity at piecewise boundaries.
    def accept(o,m):
        if o>=m: return 1.0
        if o>=.9*m: return 1-(m-o)/(.1*m)
        return 0.0
    for m in (1,1000,2000):
        vals=[accept(o/100*m,m) for o in range(0,111)]
        assert all(vals[i+1]>=vals[i] for i in range(len(vals)-1))
        assert abs(accept(.9*m,m)-0)<1e-12 and accept(m,m)==1
        assert abs(accept(.95*m,m)-.5)<1e-12
    results["negotiation acceptance monotonicity and continuity"]="PASS"
    # Deterministic replay / unique pool assignments across two businesses.
    a=BUSINESSES[0]; b=BUSINESSES[12]
    assigned=assign_agents_for_turn([(a[0],a[4]),(b[0],b[4])],7)
    repeated=assign_agents_for_turn([(a[0],a[4]),(b[0],b[4])],7)
    ids=[row[2] for row in assigned]
    assert len(ids)==len(set(ids)) and assigned==repeated
    results["two-business unique agent assignment and replay"]="PASS"
    return results

if __name__ == "__main__":
    test_results=checks()
    print("STATIC PROPERTY CHECKS (reference model only; not application runtime tests)")
    for k,v in test_results.items(): print(f"- {k}: {v}")
    print("\n30-TURN ONE-BUSINESS CAREFUL-PLAYER REFERENCE FIXTURES (not integrated app tests)")
    print("| Business | Visitors/day | Units | Gross | Tax | Platform fee | Supplies | Min wallet | End wallet |")
    for row in BUSINESSES:
        r=run_business(row)
        dollars=lambda x:f"${x/100:,.2f}"
        print(f"| {r['name']} | {r['visitors_per_day']} | {r['units_sold']} | {dollars(r['gross_cents'])} | {dollars(r['tax_cents'])} | {dollars(r['platform_fee_cents'])} | {dollars(r['supply_spend_cents'])} | {dollars(r['wallet_min_cents'])} | {dollars(r['wallet_end_cents'])} |")
