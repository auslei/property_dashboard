import streamlit as st
import pandas as pd
import textwrap
import uuid

# 1. Remove numpy_financial dependency and use standard math instead
def calculate_pmt(rate, nper, pv):
    """
    Calculates the monthly payment (Principal + Interest).
    Mimics numpy_financial.pmt but using standard math.
    """
    if rate == 0:
        return -(pv / nper)
    
    # Formula: P * (r * (1 + r)^n) / ((1 + r)^n - 1)
    # We pass negative PV to mimic the loan amount, so we return a positive payment
    pv = -pv 
    payment = (pv * rate * (1 + rate)**nper) / ((1 + rate)**nper - 1)
    return payment

st.set_page_config(page_title="Property Strategy Calculator", layout="wide")

# --- Session State for Dynamic Assets ---
if "assets" not in st.session_state:
    st.session_state.assets = [
        {
            "id": str(uuid.uuid4()),
            "name": "House 1 (Renovation Project)",
            "current_value": 1_100_000.0,
            "is_new_purchase": False,
            "purchase_price": 0.0,
            "other_capital_costs": 0.0,
            "renovation_cost": 500_000.0,
            "end_value": 2_000_000.0,
            "weekly_rent": 1000.0,
            "apply_land_tax": True,
            "land_tax": 8000.0,
            "other_annual_costs": 3000.0
        },
        {
            "id": str(uuid.uuid4()),
            "name": "House 2 (Existing Investment)",
            "current_value": 0.0,
            "is_new_purchase": True,
            "purchase_price": 1_100_000.0,
            "other_capital_costs": 70_000.0,
            "renovation_cost": 0.0,
            "end_value": 1_300_000.0,
            "weekly_rent": 1100.0,
            "apply_land_tax": True,
            "land_tax": 7000.0,
            "other_annual_costs": 2500.0
        }
    ]

def add_asset():
    st.session_state.assets.append({
        "id": str(uuid.uuid4()),
        "name": "New Asset",
        "current_value": 0.0,
        "is_new_purchase": True,
        "purchase_price": 1_000_000.0,
        "other_capital_costs": 0.0,
        "renovation_cost": 0.0,
        "end_value": 1_000_000.0,
        "weekly_rent": 500.0,
        "apply_land_tax": False,
        "land_tax": 0.0,
        "other_annual_costs": 0.0
    })

def remove_asset(asset_id):
    st.session_state.assets = [a for a in st.session_state.assets if a["id"] != asset_id]

# --- Sidebar: Inputs ---
st.sidebar.header("1. Portfolio Manager")

# Asset Management
for i, asset in enumerate(st.session_state.assets):
    # Sync name from session state if it exists to update expander label immediately
    name_key = f"name_{asset['id']}"
    if name_key in st.session_state:
        asset["name"] = st.session_state[name_key]

    # Ensure unique label for expander
    label = f"{asset['name']} (#{i+1})"
    with st.sidebar.expander(label, expanded=False):
        # We don't need to assign the result back to asset["name"] here if we rely on the sync above,
        # but keeping it doesn't hurt and ensures consistency if the key was missing.
        st.text_input("Name", value=asset["name"], key=name_key)
        
        asset["is_new_purchase"] = st.checkbox("Is this a new purchase?", value=asset["is_new_purchase"], key=f"new_{asset['id']}")
        
        if asset["is_new_purchase"]:
            asset["purchase_price"] = st.number_input("Purchase Price ($)", value=float(asset["purchase_price"]), step=100000.0, key=f"price_{asset['id']}")
            asset["other_capital_costs"] = st.number_input("Other Capital Costs ($)", value=float(asset.get("other_capital_costs", 0.0)), step=1000.0, help="Legal fees, due diligence, etc.", key=f"other_cap_{asset['id']}")
            asset["current_value"] = 0.0 # New purchases have no 'current' value in the portfolio yet
        else:
            asset["current_value"] = st.number_input("Current Value ($)", value=float(asset["current_value"]), step=100000.0, key=f"curr_{asset['id']}")
            asset["purchase_price"] = 0.0
            asset["other_capital_costs"] = 0.0
            
        asset["renovation_cost"] = st.number_input("Renovation/Build Cost ($)", value=float(asset["renovation_cost"]), step=10000.0, key=f"reno_{asset['id']}")
        
        # Default end value to purchase price or current value if not set
        default_end = asset["purchase_price"] if asset["is_new_purchase"] else asset["current_value"]
        if asset["end_value"] == 0: asset["end_value"] = default_end
            
        asset["end_value"] = st.number_input("Value After Works ($)", value=float(asset["end_value"]), step=100000.0, help="Expected value after renovation/build", key=f"end_{asset['id']}")
        
        asset["weekly_rent"] = st.number_input("Est. Weekly Rent ($)", value=float(asset["weekly_rent"]), step=50.0, key=f"rent_{asset['id']}")
        
        # Annual Expenses
        st.markdown("**Annual Expenses**")
        asset["apply_land_tax"] = st.checkbox("Subject to Land Tax?", value=asset.get("apply_land_tax", False), key=f"apply_tax_{asset['id']}")
        
        if asset["apply_land_tax"]:
            asset["land_tax"] = st.number_input("Est. Annual Land Tax ($)", value=float(asset.get("land_tax", 0.0)), step=100.0, key=f"tax_{asset['id']}")
        else:
            asset["land_tax"] = 0.0
            
        asset["other_annual_costs"] = st.number_input("Other Annual Costs ($)", value=float(asset.get("other_annual_costs", 0.0)), step=100.0, help="Insurance, Management Fees, Maintenance, etc.", key=f"other_ann_{asset['id']}")
        
        if st.button("Remove Asset", key=f"rem_{asset['id']}"):
            remove_asset(asset["id"])
            st.rerun()

st.sidebar.button("➕ Add Asset", on_click=add_asset)

st.sidebar.markdown("---")
st.sidebar.subheader("Global Settings")
current_debt = st.sidebar.number_input("Existing Portfolio Debt ($)", value=900_000.0, step=10000.0)

st.sidebar.subheader("Loan Settings")
interest_rate = st.sidebar.slider("Interest Rate (%)", 4.0, 9.0, 6.0, 0.1) / 100
loan_term = st.sidebar.slider("Loan Term (Years)", 10, 30, 30)
stamp_duty_rate = st.sidebar.slider("Stamp Duty & Costs (%)", 0.0, 7.0, 5.5, 0.1) / 100

st.sidebar.subheader("Cash Flow Strategy")

# --- Calculations (Aggregated) ---
total_assets_current = sum(a["current_value"] for a in st.session_state.assets)
total_assets_future = sum(a["end_value"] for a in st.session_state.assets)
total_build_cost = sum(a["renovation_cost"] for a in st.session_state.assets)
total_purchase_costs = sum(a["purchase_price"] for a in st.session_state.assets)
total_other_capital = sum(a.get("other_capital_costs", 0.0) for a in st.session_state.assets)
total_land_tax = sum(a.get("land_tax", 0.0) for a in st.session_state.assets)
total_other_annual_costs = sum(a.get("other_annual_costs", 0.0) for a in st.session_state.assets)
total_stamp_duty = total_purchase_costs * stamp_duty_rate

# Debt Calculation
committed_debt = current_debt + total_build_cost + total_purchase_costs + total_other_capital + total_stamp_duty

# Calculate Base LVR (Minimum possible)
if total_assets_future > 0:
    base_lvr = (committed_debt / total_assets_future) * 100
else:
    base_lvr = 0.0

# Determine Slider Range
min_lvr = float(base_lvr)
max_lvr = 80.0

# LVR Slider Logic
if min_lvr > max_lvr:
    # If committed debt already exceeds 80% LVR, we can't target 80%.
    # We must set the target to at least the current committed LVR.
    st.sidebar.warning(f"Base LVR is {min_lvr:.1f}%, which is > 80%. Slider disabled.")
    target_lvr = min_lvr
else:
    target_lvr = st.sidebar.slider("Target LVR (%)", min_value=min_lvr, max_value=max_lvr, value=min_lvr, step=0.1, format="%.1f%%")

# Calculate Buffer based on Target LVR
# Target Debt = Assets * (Target LVR / 100)
# Buffer = Target Debt - Committed Debt
target_debt = total_assets_future * (target_lvr / 100)
buffer_cash = target_debt - committed_debt

if buffer_cash < 0:
    buffer_cash = 0.0

st.sidebar.metric("Cash Buffer Released", f"${buffer_cash:,.0f}")

buffer_is_offset = st.sidebar.checkbox("Keep Buffer in Offset Account?", value=True, help="If checked, the buffer cash reduces the interest payable (Interest Only loans).")

total_debt_future = committed_debt + buffer_cash

# 3. LVR & Equity
lvr_current = (current_debt / total_assets_current * 100) if total_assets_current > 0 else 0
lvr_future = (total_debt_future / total_assets_future * 100) if total_assets_future > 0 else 0
equity_future = total_assets_future - total_debt_future

# 4. Repayments
monthly_rate = interest_rate / 12
n_periods = loan_term * 12

# Interest Only
effective_debt_io = total_debt_future
if buffer_is_offset:
    effective_debt_io -= buffer_cash

pmt_io = effective_debt_io * monthly_rate

# P&I
pmt_pi = calculate_pmt(monthly_rate, n_periods, -total_debt_future)

# --- Main Dashboard ---

st.title("Property Portfolio Strategy Dashboard")
st.markdown("### Dynamic Portfolio Analysis")

# Top Level Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Assets (Future)", f"${total_assets_future/1_000_000:.2f}M", delta=f"+${(total_assets_future - total_assets_current)/1_000_000:.2f}M")
col2.metric("Total Debt (Future)", f"${total_debt_future/1_000_000:.2f}M", delta=f"+${(total_debt_future - current_debt)/1_000_000:.2f}M", delta_color="inverse")
col3.metric("New LVR", f"{lvr_future:.1f}%", delta=f"{lvr_future - lvr_current:.1f}%", delta_color="inverse")
col4.metric("Net Equity", f"${equity_future/1_000_000:.2f}M")

# LVR Warning
if lvr_future > 80:
    st.error(f"⚠️ WARNING: LVR is {lvr_future:.1f}%. This is above the 80% safety threshold. You will likely pay LMI (Lenders Mortgage Insurance) and face stricter lending criteria.")
elif lvr_future > 60:
    st.success(f"✅ LVR is {lvr_future:.1f}%. This is a healthy range for equity release.")
else:
    st.info(f"ℹ️ LVR is {lvr_future:.1f}%. Very conservative position.")

st.divider()

# --- Tabs for detailed analysis ---
tab1, tab2, tab3, tab4 = st.tabs(["💰 Cash Flow Analysis", "📈 Capitalizing Interest (Risk Sim)", "📋 Portfolio Details", "🚀 Optimization"])

with tab1:
    st.header("Can you afford the debt?")
    st.write(f"Total Loan Amount: **${total_debt_future:,.0f}** (Includes Stamp Duty + ${buffer_cash:,.0f} Cash Buffer)")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Option A: Interest Only")
        st.metric("Monthly Payment", f"${pmt_io:,.0f}")
        st.caption("Keeps debt constant. Good for cash flow during construction.")
        if buffer_is_offset:
            st.success("✅ Offset Active: Interest calculated on reduced balance.")
        
    with c2:
        st.subheader("Option B: Principal & Interest")
        st.metric("Monthly Payment", f"${pmt_pi:,.0f}")
        st.caption(f"Pays off debt over {loan_term} years. Higher monthly commitment.")
        
    st.write("---")
    st.subheader("Rental Gap Calculator")
    st.write("How much rent do you need to cover the interest?")
    
    total_monthly_rent = sum(a["weekly_rent"] for a in st.session_state.assets) * 52 / 12
    monthly_land_tax = total_land_tax / 12
    monthly_other_costs = total_other_annual_costs / 12
    total_monthly_expenses = monthly_land_tax + monthly_other_costs
    
    # Net Monthly Income (Rent - Expenses)
    net_monthly_income = total_monthly_rent - total_monthly_expenses
    
    gap_io = pmt_io - net_monthly_income
    gap_pi = pmt_pi - net_monthly_income
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Monthly Rent", f"${total_monthly_rent:,.0f}")
    col_a.caption(f"Less Expenses: -${total_monthly_expenses:,.0f}/m")
    
    col_b.metric("IO Shortfall", f"-${gap_io:,.0f}", delta_color="off")
    col_c.metric("P&I Shortfall", f"-${gap_pi:,.0f}", delta_color="off")
    
    if gap_io > 0:
        st.warning(f"You need to find **${gap_io:,.0f} per month** from your salary to just pay the interest.")
        
        # Buffer Logic
        if buffer_cash > 1.0:
            months_survival = buffer_cash / gap_io
            years_survival = months_survival / 12
            
            st.info(textwrap.dedent(f"""
                🛡️ **Buffer Strategy Active:** You borrowed an extra **\${buffer_cash:,.0f}**. 
                Using this to pay the \${gap_io:,.0f} monthly shortfall, your buffer will last:
                
                ### **{months_survival:.1f} Months** ({years_survival:.1f} Years)
                
                Before you need to use your own salary.
            """))
        else:
            st.markdown("*Tip: Try adding a 'Cash Buffer' in the sidebar to see how long borrowed cash could cover this gap.*")
            
    else:
        st.success("Rental income covers the interest bill! The portfolio is neutrally geared.")

with tab2:
    st.header("Simulation: Capitalizing Interest")
    st.markdown(textwrap.dedent("""
        This simulates the **"Debt Spiral"** vs **"Growth"**. 
        It assumes you borrow the money to pay the interest bill every year (beyond your initial buffer).
    """))
    
    sim_years = st.slider("Simulation Years", 5, 20, 10)
    growth_rate = st.slider("Projected Annual Property Growth (%)", -2.0, 12.0, 5.0, 0.5) / 100
    
    # Simulation Logic
    years = list(range(sim_years + 1))
    sim_data = []
    
    # Initialize individual asset tracking
    # Structure: {asset_name: [value_year_0, value_year_1, ...]}
    asset_growth_data = {a["name"]: [a["end_value"]] for a in st.session_state.assets}
    
    curr_debt = total_debt_future
    
    for y in years:
        # Calculate total assets for this year
        curr_total_assets = sum(values[-1] for values in asset_growth_data.values())
        
        # Store simulation data
        lvr = (curr_debt / curr_total_assets) * 100 if curr_total_assets > 0 else 0
        equity = curr_total_assets - curr_debt
        sim_data.append([y, curr_total_assets, curr_debt, equity, lvr])
        
        if y < sim_years:
            # Calculate next year's values
            
            # 1. Grow each asset
            for name, values in asset_growth_data.items():
                new_value = values[-1] * (1 + growth_rate)
                values.append(new_value)
            
            # 2. Grow debt (Capitalize Interest)
            interest_bill = curr_debt * interest_rate
            curr_debt += interest_bill
        
    df_sim = pd.DataFrame(sim_data, columns=["Year", "Assets", "Debt", "Equity", "LVR"])
    
    # Metrics: Equity Gain
    initial_equity = df_sim.iloc[0]["Equity"]
    final_equity = df_sim.iloc[-1]["Equity"]
    equity_gain = final_equity - initial_equity
    
    st.metric("Total Equity Gain (over simulation)", f"${equity_gain/1_000_000:.2f}M", delta=f"{((final_equity/initial_equity)-1)*100:.1f}% Growth")
    
    # Charts
    st.subheader("Net Equity Growth")
    st.area_chart(df_sim, x="Year", y="Equity", color="#2ecc71")
    
    st.subheader("Individual Property Growth")
    # Prepare data for line chart: Year as index, columns are asset names
    df_assets = pd.DataFrame(asset_growth_data)
    df_assets["Year"] = years
    st.line_chart(df_assets, x="Year", y=[a["name"] for a in st.session_state.assets])
    
    st.subheader("Asset vs Debt Growth")
    st.line_chart(df_sim, x="Year", y=["Assets", "Debt"])
    
    st.subheader("LVR Projection")
    st.line_chart(df_sim, x="Year", y="LVR")
    
    final_lvr = df_sim.iloc[-1]["LVR"]
    if final_lvr > 80:
        st.error(f"CRITICAL RISK: By year {sim_years}, your LVR hits {final_lvr:.1f}%. The bank may force you to sell.")
    elif growth_rate < interest_rate:
        st.warning(f"Warning: Interest Rate ({interest_rate*100}%) is higher than Growth ({growth_rate*100}%). You are slowly losing equity.")
    else:
        st.success(f"Strategy Winning: Growth ({growth_rate*100}%) is beating Interest ({interest_rate*100}%). Equity is compounding.")

with tab3:
    st.header("Portfolio Details")
    
    # Create a summary dataframe from the assets list
    asset_data = []
    for a in st.session_state.assets:
        asset_data.append({
            "Name": a["name"],
            "Current Value": a["current_value"],
            "Purchase Price": a["purchase_price"],
            "Other Capital Costs": a.get("other_capital_costs", 0.0),
            "Reno Cost": a["renovation_cost"],
            "End Value": a["end_value"],
            "Weekly Rent": a["weekly_rent"],
            "Land Tax": a.get("land_tax", 0.0),
            "Other Annual Costs": a.get("other_annual_costs", 0.0)
        })
    
    st.dataframe(pd.DataFrame(asset_data))
    
    st.subheader("Debt Breakdown")
    st.dataframe(pd.DataFrame({
        "Item": ["Existing Debt", "New Purchase Costs", "Other Capital Costs", "Renovation Costs", "Stamp Duty", "Cash Buffer"],
        "Amount": [current_debt, total_purchase_costs, total_other_capital, total_build_cost, total_stamp_duty, buffer_cash]
    }))

with tab4:
    st.header("🚀 Loan Structuring & Optimization")
    st.markdown("### Can you 'Uncross' your loans?")
    st.markdown(textwrap.dedent("""
        **Goal:** Attribute debt to specific properties to avoid "Cross-Collateralization". 
        Ideally, each property should stand alone with a loan of **≤ 80%** of its value.
    """))
    
    # 1. Calculate Capacity
    structure_data = []
    total_capacity_80 = 0
    
    # We need to allocate the ACTUAL total debt (future) across these assets
    remaining_debt_to_allocate = total_debt_future
    
    # First pass: Calculate limits
    asset_calcs = []
    for a in st.session_state.assets:
        val = a["end_value"]
        limit_80 = val * 0.80
        total_capacity_80 += limit_80
        asset_calcs.append({
            "name": a["name"],
            "value": val,
            "limit_80": limit_80,
            "allocated_debt": 0.0
        })
        
    # 2. Allocation Logic
    # Strategy: Fill up to 80% first? Or Pro-rata?
    # "Uncrossing" usually means maxing out the highest growth/safest assets or just spreading it.
    # Let's try a "Safe Standalone" approach:
    # If Total Debt <= Total Capacity, we can uncross.
    # We will allocate debt proportional to value, but capped at 80%.
    
    is_uncrossing_possible = total_debt_future <= total_capacity_80
    
    if is_uncrossing_possible:
        st.success(f"✅ **Uncrossing is Possible!** Your Total Debt (\${total_debt_future:,.0f}) is less than your Total Borrowing Capacity at 80% LVR (\${total_capacity_80:,.0f}).")
        
        # Allocate proportional to value (to keep LVRs even)
        for item in asset_calcs:
            # Ideal share = (Item Value / Total Value) * Total Debt
            # This naturally keeps LVR constant across all assets if possible
            share = (item["value"] / total_assets_future) * total_debt_future
            item["allocated_debt"] = share
            
    else:
        st.warning(f"⚠️ **Cross-Collateralization Required.** You owe \${total_debt_future:,.0f}, but banks will only lend \${total_capacity_80:,.0f} at 80% LVR. You are over the 80% threshold globally.")
        
        # Allocate 80% to everything (max out)
        for item in asset_calcs:
            item["allocated_debt"] = item["limit_80"]
            remaining_debt_to_allocate -= item["limit_80"]
            
        # The remaining debt is "Unsecured" or "Over 80%" (LMI territory)
        # We just add it to the first asset or spread it? 
        # Let's spread the excess pro-rata to show the pain shared, or highlight it separately.
        # For simplicity in this view, let's add it to the largest asset or just show it as "Excess".
        # Actually, let's just distribute it pro-rata on top of the 80%.
        excess_debt = total_debt_future - total_capacity_80
        for item in asset_calcs:
            extra = (item["value"] / total_assets_future) * excess_debt
            item["allocated_debt"] += extra

    # 3. Build Display Data
    for item in asset_calcs:
        lvr_individual = (item["allocated_debt"] / item["value"] * 100) if item["value"] > 0 else 0
        status = "✅ Standalone" if lvr_individual <= 80 else "⚠️ Crossed / LMI"
        
        structure_data.append({
            "Asset": item["name"],
            "Market Value": f"${item['value']:,.0f}",
            "Max Loan (80%)": f"${item['limit_80']:,.0f}",
            "Allocated Debt": f"${item['allocated_debt']:,.0f}",
            "Resulting LVR": f"{lvr_individual:.1f}%",
            "Status": status
        })
        
    st.table(pd.DataFrame(structure_data))
    
    # 4. Visuals
    st.subheader("Visualizing the Structure")
    
    # Prepare data for bar chart: Asset vs Debt
    chart_data = pd.DataFrame(asset_calcs)
    chart_data = chart_data[["name", "value", "allocated_debt"]]
    chart_data.columns = ["Asset", "Asset Value", "Allocated Debt"]
    
    # Melt for Streamlit bar chart
    chart_data_melted = chart_data.melt("Asset", var_name="Type", value_name="Amount")
    
    st.bar_chart(chart_data_melted, x="Asset", y="Amount", color="Type", stack=False)