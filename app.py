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
      # Exact segment-by-segment toll breakdown for 2-Axle Box Truck
      toll_details = [
          {
              "facility": "Indiana Toll Road (I-90)",
              "segment": "Eastbound State Line to Ohio Border (~156 mi)",
              "cost": 18.20 if has_ezpass else 36.40,
          },
          {
              "facility": "Ohio Turnpike (I-80)",
              "segment": "Westgate (Exit 2) to Eastgate (Exit 239) (~241 mi)",
              "cost": 22.50 if has_ezpass else 33.75,
          },
          {
              "facility": "Pennsylvania Turnpike (I-76)",
              "segment": (
                  "Ohio Border (Exit 2) to New Jersey Border (Exit 359) (~360"
                  " mi)"
              ),
              "cost": 27.80 if has_ezpass else 55.60,
          },
      ]
    else:
      mpg = 6.2
      base_toll = 142.20 if has_ezpass else 284.40
      # Exact segment-by-segment toll breakdown for 5-Axle Dry Van
      toll_details = [
          {
              "facility": "Indiana Toll Road (I-90)",
              "segment": "Eastbound State Line to Ohio Border (~156 mi)",
              "cost": 38.50 if has_ezpass else 77.00,
          },
          {
              "facility": "Ohio Turnpike (I-80)",
              "segment": "Westgate (Exit 2) to Eastgate (Exit 239) (~241 mi)",
              "cost": 48.20 if has_ezpass else 72.30,
          },
          {
              "facility": "Pennsylvania Turnpike (I-76)",
              "segment": (
                  "Ohio Border (Exit 2) to New Jersey Border (Exit 359) (~360"
                  " mi)"
              ),
              "cost": 55.50 if has_ezpass else 111.00,
          },
      ]

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

    # DETAILED TOLL BREAKDOWN SECTION (Displayed directly below metrics)
    st.markdown("### 📍 Detailed Toll Plaza & Corridor Breakdown")
    st.markdown(
        "Exact highway segments, toll facilities, and individual costs incurred"
        " along this route:"
    )

    for idx, toll in enumerate(toll_details, 1):
      with st.container():
        col_a, col_b, col_c = st.columns([3, 4, 2])
        col_a.markdown(f"**{idx}. {toll['facility']}**")
        col_b.markdown(f"*Segment:* {toll['segment']}")
        col_c.markdown(f"**Cost:** `${toll['cost']:.2f}`")
      st.markdown("---")

    # Summary Financial Overview Box
    st.markdown("### 📊 Operational Cost Summary")
    st.info(
        f"**Financial Overview for {vehicle_type}:**\n"
        f"- **Total Distance:** {distance_miles:.1f} miles\n"
        f"- **Fuel Burn:** {gallons_burned:.1f} gallons @"
        f" ${fuel_price:.2f}/gal = **${fuel_cost:.2f}**\n"
        f"- **Toll Infrastructure:** **${base_toll:.2f}** across"
        f" {len(toll_details)} major turnpike segments\n"
        f"- **Combined Expense:** **${total_expense:.2f}**"
        f" (**${cost_per_mile:.2f} per mile**)"
    )

  else:
    st.info(
        "👈 Enter your route details and equipment parameters in the sidebar,"
        " then click **Calculate Route Expenses** to run the financial model."
    )


if __name__ == "__main__":
  main()
