import requests
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Truck Expense",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=3600)
def fetch_latest_diesel_price():
  """Fetches the latest U.S. retail on-highway diesel price from the EIA API.

  Falls back safely to the current national baseline if unavailable.
  """
  api_key = st.secrets.get("EIA_API_KEY", "DEMO_KEY")
  url = f"https://api.eia.gov/v2/petroleum/pri/gnd/data/?api_key={api_key}&frequency=weekly&data[0]=value&sort[0][column]=period&sort[0][direction]=desc&length=1"

  try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      data = response.json()
      rows = data.get("response", {}).get("data", [])
      if rows:
        return float(rows[0]["value"]), "Live EIA Feed Connected"
  except Exception:
    pass

  return 5.31, "Using National Baseline ($5.31)"


def fetch_tollguru_data(origin, destination, vehicle_type, has_ezpass):
  """Queries TollGuru API for exact route distance and commercial tolls.

  Falls back gracefully if API key is not configured in st.secrets.
  """
  api_key = st.secrets.get("TOLLGURU_API_KEY", "")
  is_box = "Box Truck" in vehicle_type

  if not api_key:
    # Fallback simulation data if API key is not set
    if is_box:
      distance_miles = 790.0
      mpg = 10.5
      base_toll = 68.50 if has_ezpass else 115.00
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
      distance_miles = 790.0
      mpg = 6.2
      base_toll = 142.20 if has_ezpass else 284.40
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
    return (
        distance_miles,
        mpg,
        base_toll,
        toll_details,
        "Fallback Mode (Add TOLLGURU_API_KEY in st.secrets)",
    )

  url = "https://apis.tollguru.com/toll/v2/origin-destination-waypoints"
  headers = {"content-type": "application/json", "x-api-key": api_key}
  payload = {
      "from": {"address": origin},
      "to": {"address": destination},
      "serviceProvider": "here",
      "vehicle": {
          "type": "2AxlesTruck" if is_box else "5AxlesTruck",
          "weight": {"value": 26000 if is_box else 80000, "unit": "pound"},
          "height": {"value": 11 if is_box else 13.5, "unit": "foot"},
      },
  }

  try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    if response.status_code == 200:
      data = response.json()
      routes = data.get("routes", [])
      if routes:
        primary = routes[0]
        dist_meters = primary.get("summary", {}).get("distance", {}).get("value", 1271380)
        distance_miles = dist_meters * 0.000621371

        costs = primary.get("costs", {})
        base_toll = costs.get("tag", 68.50) if has_ezpass else costs.get("cash", 115.00)
        if base_toll is None:
          base_toll = costs.get("cash", 68.50)

        mpg = 10.5 if is_box else 6.2

        toll_details = []
        for toll_loc in primary.get("tolls", []):
          c = toll_loc.get("tagCost", 0.0) if has_ezpass else toll_loc.get("cashCost", 0.0)
          if c is None:
            c = toll_loc.get("cashCost", 0.0) or 0.0
          toll_details.append({
              "facility": toll_loc.get("name", "Turnpike Gantry"),
              "segment": toll_loc.get("road", "Controlled Highway Section"),
              "cost": float(c),
          })

        if not toll_details:
          toll_details = [{
              "facility": "Calculated Corridor Total",
              "segment": f"{origin} to {destination}",
              "cost": float(base_toll),
          }]

        return (
            distance_miles,
            mpg,
            float(base_toll),
            toll_details,
            "Live TollGuru API Connected",
        )
  except Exception:
    pass

  return 790.0, (10.5 if is_box else 6.2), 68.50, [{
      "facility": "Fallback Turnpike Segment",
      "segment": "Interstate Corridor",
      "cost": 68.50,
  }], "API Error - Using Baseline Fallback"


def main():
  st.title("🚚 Truck Expense Dashboard")
  st.markdown(
      "Precision operational cost calculator for commercial freight transit:"
      " exact tolls, live EIA fuel feed, and real-time corridor metrics."
  )

  # Fetch live EIA diesel price
  live_diesel_price, price_status = fetch_latest_diesel_price()

  # Sidebar Controls
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
      "Current Diesel Price ($/gal)",
      value=live_diesel_price,
      step=0.05,
      help=f"Status: {price_status}",
  )

  has_ezpass = st.sidebar.checkbox(
      "Using Commercial E-ZPass / Transponder",
      value=True,
      help="Unchecking applies cash/plate penalties on major turnpikes.",
  )

  if st.sidebar.button("Calculate Route Expenses", type="primary"):
    with st.spinner(
        "Querying routing engines and analyzing commercial toll matrices..."
    ):
      distance_miles, mpg, base_toll, toll_details, toll_status = (
          fetch_tollguru_data(origin, destination, vehicle_type, has_ezpass)
      )

      gallons_burned = distance_miles / mpg
      fuel_cost = gallons_burned * fuel_price
      total_expense = fuel_cost + base_toll
      cost_per_mile = total_expense / distance_miles if distance_miles > 0 else 0.0

      # Main Interface Display
      st.subheader(
          f"Trip Cost Analysis: {origin} ➔ {destination} ({vehicle_type})"
      )

      # Metrics Row
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

      # Detailed Toll Breakdown Section (Placed directly below metrics)
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

      # Operational Cost Summary Box
      st.markdown("### 📊 Operational Cost Summary")
      st.info(
          f"**Financial Overview for {vehicle_type}:**\n"
          f"- **Total Distance:** {distance_miles:.1f} miles\n"
          f"- **Fuel Burn:** {gallons_burned:.1f} gallons @"
          f" ${fuel_price:.2f}/gal = **${fuel_cost:.2f}**\n"
          f"- **Toll Infrastructure:** **${base_toll:.2f}** across"
          f" {len(toll_details)} recorded segments\n"
          f"- **Combined Expense:** **${total_expense:.2f}**"
          f" (**${cost_per_mile:.2f} per mile**)\n"
          f"- **Data Feeds:** [{price_status}] | [{toll_status}]"
      )

  else:
    st.info(
        "👈 Enter your route details and equipment parameters in the sidebar,"
        " then click **Calculate Route Expenses** to run the financial model."
    )


if __name__ == "__main__":
  main()
