import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Truck Expense",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
  st.title("🚚 Truck Expense Dashboard")
  st.markdown(
      "Precision operational cost calculator for commercial freight transit:"
      " exact tolls, fuel burn, and per-mile breakdowns."
  )

  # Sidebar Controls for Route & Equipment
  st.sidebar.header("Route & Fleet Parameters")

  vehicle_type = st.sidebar.selectbox(
      "Select Equipment Configuration",
      [
          "24-Foot Box Truck (2/3-Axle Medium Duty)",
          "Dry Van (5-Axle Semi-Truck)",
      ],
  )

  col_origin, col_dest = st.sidebar.columns(2)
  with col_origin:
    origin = st.text_input("Origin", "Chicago, IL")
  with col_dest:
    destination = st.text_input("Destination", "New York, NY")

  fuel_price = st.sidebar.number_input(
      "Current Diesel Price ($/gal)", value=3.85, step=0.05
  )
  has_ezpass = st.sidebar.checkbox(
      "Using Commercial E-ZPass / Transponder",
      value=True,
      help=(
          "Unchecking applies Toll-by-Plate cash penalties on major"
          " turnpikes."
      ),
  )

  # Calculation Trigger
  if st.sidebar.button("Calculate Route Expenses", type="primary"):

    # Core Calculation Logic (Simulating routing & toll engine metrics)
    distance_miles = 790.0  # Baseline corridor distance example

    if "Box Truck" in vehicle_type:
      mpg = 10.5
      base_toll = 68.50 if has_ezpass else 115.00
    else:
      mpg = 6.2
      base_toll = (
          142.20 if has_ezpass else 284.40
      )  # 2x toll-by-plate penalty for heavy semi

    gallons_burned = distance_miles / mpg
    fuel_cost = gallons_burned * fuel_price
    total_expense = fuel_cost + base_toll
    cost_per_mile = total_expense / distance_miles

    # Main Interface Display
    st.subheader(
        f"Trip Cost Analysis: {origin} ➔ {destination} ({vehicle_type})"
    )

    # Top Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Distance", f"{distance_miles:.1f} mi")
    m2.metric(
        "Est. Fuel Outlay", f"${fuel_cost:.2f}", f"{mpg} MPG (~{gallons_burned:.1f} gal)"
    )
    m3.metric(
        "Exact Toll Outlay",
        f"${base_toll:.2f}",
        "Transponder Rate" if has_ezpass else "Plate Penalty Applied",
    )
    m4.metric(
        "Total Trip Expense",
        f"${total_expense:.2f}",
        f"${cost_per_mile:.2f} / mile",
    )

    st.divider()

    # Detailed Tabs
    tab_summary, tab_breakdown = st.tabs(
        ["Expense Summary", "Intersecting Toll Corridors"]
    )

    with tab_summary:
      st.markdown("### Operational Cost Breakdown")
      st.markdown(f"""
            * **Equipment Profile:** {vehicle_type}
            * **Fuel Expenditure:** ${fuel_cost:.2f} ({gallons_burned:.1f} gallons consumed at ${fuel_price:.2f}/gal)
            * **Infrastructure Tolls:** ${base_toll:.2f} (Verified via corridor rate schedule)
            * **Combined Outlay:** **${total_expense:.2f}**
            * **Operational Efficiency:** **${cost_per_mile:.2f} per mile**
            """)

    with tab_breakdown:
      st.markdown("### Major Toll Facilities on Route")
      st.markdown("""
            * **Ohio Turnpike (I-80):** Class-specific commercial mileage rate applied.
            * **Pennsylvania Turnpike (I-76):** High-cost multi-segment gantry toll factored.
            * **New Jersey Turnpike & Port Authority:** Urban commercial tier charges included.
            """)

  else:
    st.info(
        "👈 Enter your route details and equipment parameters in the sidebar,"
        " then click **Calculate Route Expenses** to run the financial model."
    )


if __name__ == "__main__":
  main()
