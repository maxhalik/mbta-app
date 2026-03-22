import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime
import time
import os

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MBTA Commuter Rail Tracker",
    page_icon="🚂",
    layout="wide",
)

# ── Your API key ──────────────────────────────────────────────────────────────
# Get a free key at: https://api-v3.mbta.com/register
# Then replace the string below with your key.

API_KEY = st.secrets.get("MBTA_API_KEY", os.getenv("MBTA_API_KEY", ""))

# ── Route colors (matches MBTA branding) ─────────────────────────────────────
ROUTE_COLORS = {
    "CR-Fairmount":    "#3572b0",
    "CR-Fitchburg":    "#3572b0",
    "CR-Franklin":     "#3572b0",
    "CR-Greenbush":    "#3572b0",
    "CR-Haverhill":    "#3572b0",
    "CR-Kingston":     "#3572b0",
    "CR-Lowell":       "#3572b0",
    "CR-Middleborough":"#3572b0",
    "CR-Needham":      "#3572b0",
    "CR-Newburyport":  "#3572b0",
    "CR-Providence":   "#3572b0",
    "CR-Worcester":    "#3572b0",
}

STATUS_LABELS = {
    "INCOMING_AT":   "Arriving at",
    "STOPPED_AT":    "Stopped at",
    "IN_TRANSIT_TO": "In transit to",
}

# ── Data fetching ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=20)   # cache for 20 seconds, then re-fetch
def get_trains(api_key: str):
    """Fetch all active commuter rail vehicles from the MBTA API."""
    try:
        response = requests.get(
            "https://api-v3.mbta.com/vehicles",
            params={
                "filter[route_type]": 2,   # 2 = Commuter Rail
                "include": "route,stop",
                "api_key": api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)


def get_stops(api_key: str):
    """Fetch stop names so we can label 'next stop' nicely."""
    try:
        response = requests.get(
            "https://api-v3.mbta.com/stops",
            params={
                "filter[route_type]": 2,
                "api_key": api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        stops = {}
        for stop in response.json()["data"]:
            stops[stop["id"]] = stop["attributes"]["name"]
        return stops
    except Exception:
        return {}


# ── Build the map ─────────────────────────────────────────────────────────────
def build_map(trains_data, stops_lookup, selected_route):
    m = folium.Map(
        location=[42.36, -71.06],
        zoom_start=10,
        tiles="CartoDB positron",   # clean light basemap
    )

    active_count = 0

    for train in trains_data["data"]:
        attrs = train["attributes"]
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")

        # Skip trains with no position yet
        if lat is None or lon is None:
            continue

        route_id = (
            train.get("relationships", {})
                 .get("route", {})
                 .get("data", {})
                 .get("id", "Unknown")
        )

        # Filter by selected route if user chose one
        if selected_route != "All Lines" and route_id != selected_route:
            continue

        active_count += 1

        stop_id = (
            train.get("relationships", {})
                 .get("stop", {})
                 .get("data", {})
                 .get("id", None)
        )
        stop_name = stops_lookup.get(stop_id, stop_id or "Unknown stop")

        status_raw = attrs.get("current_status", "")
        status = STATUS_LABELS.get(status_raw, status_raw)
        label = attrs.get("label", "?")
        speed = attrs.get("speed")
        bearing = attrs.get("bearing", 0)
        updated = attrs.get("updated_at", "")

        # Format the updated time nicely
        try:
            dt = datetime.fromisoformat(updated)
            updated_str = dt.strftime("%-I:%M:%S %p")
        except Exception:
            updated_str = updated

        speed_str = f"{speed:.0f} mph" if speed is not None else "N/A"
        route_short = route_id.replace("CR-", "") if route_id else "Unknown"
        color = ROUTE_COLORS.get(route_id, "#555555")

        # Popup HTML
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 180px;">
            <b style="font-size:15px;">🚂 Train {label}</b><br>
            <span style="color:#555; font-size:12px;">{route_short} Line</span><br><br>
            <b>{status}</b> {stop_name}<br>
            <span style="font-size:12px;">Speed: {speed_str}</span><br>
            <span style="font-size:11px; color:#888;">Updated: {updated_str}</span>
        </div>
        """

        # Draw a circle marker for the train
        folium.CircleMarker(
            location=[lat, lon],
            radius=9,
            color="white",
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=f"Train {label} — {route_short} Line",
            popup=folium.Popup(popup_html, max_width=250),
        ).add_to(m)

    return m, active_count


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🚂 MBTA Commuter Rail Tracker")
st.caption("Live train positions — updates every 20 seconds")

# Sidebar controls
with st.sidebar:
    st.header("Filters")

    all_routes = [
        "All Lines",
        "CR-Fairmount",
        "CR-Fitchburg",
        "CR-Franklin",
        "CR-Greenbush",
        "CR-Haverhill",
        "CR-Kingston",
        "CR-Lowell",
        "CR-Middleborough",
        "CR-Needham",
        "CR-Newburyport",
        "CR-Providence",
        "CR-Worcester",
    ]

    selected_route = st.selectbox(
        "Filter by line:",
        options=all_routes,
        format_func=lambda x: x.replace("CR-", "") if x != "All Lines" else x,
    )

    st.divider()
    st.markdown("**About**")
    st.markdown(
        "Data from the [MBTA V3 API](https://api-v3.mbta.com/docs/swagger). "
        "Click any train marker for details."
    )
    st.markdown("Positions update every ~20 seconds.")

# Fetch data
trains_data, error = get_trains(API_KEY)

if error:
    st.error(f"Couldn't reach the MBTA API: {error}")
    st.stop()

if API_KEY == "YOUR_API_KEY_HERE":
    st.warning(
        "⚠️ You haven't added your API key yet! "
        "Get a free one at https://api-v3.mbta.com/register and paste it into app.py."
    )

stops_lookup = get_stops(API_KEY)

# Build and display the map
m, active_count = build_map(trains_data, stops_lookup, selected_route)

col1, col2, col3 = st.columns(3)
col1.metric("Active Trains", active_count)
col2.metric("Last Updated", datetime.now().strftime("%-I:%M:%S %p"))
col3.metric("Line", selected_route.replace("CR-", "") if selected_route != "All Lines" else "All")

st_folium(m, width="100%", height=560, returned_objects=[])

# Auto-refresh every 20 seconds
time.sleep(20)
st.rerun()
