import streamlit as st
import requests
from datetime import  date, timedelta
from pathlib import Path
import plotly.graph_objects as go

API_KEY = "1a18b6c5c60840b9af470731250806"
BASE_URL = "http://api.weatherapi.com/v1"

# Initialize favorites in session state
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

# Page config
st.set_page_config(page_title="Weather App", page_icon="🌦️", layout="wide")

# Sidebar - Favorites & Weather Settings
st.sidebar.title("⚙️ Weather Settings")

# Favorite cities selectbox
if st.session_state.favorites:
    selected_fav = st.sidebar.selectbox("Select Favorite City", [""] + st.session_state.favorites)
else:
    selected_fav = ""

# Determine city: if favorite selected, use it; else text input
if selected_fav:
    city = selected_fav
else:
    city = st.sidebar.text_input("Enter city name", "New York")

# Add / Remove Favorites buttons below city input
if city and city not in st.session_state.favorites:
    if st.sidebar.button("Add to Favorites"):
        st.session_state.favorites.append(city)
        st.rerun()

if city in st.session_state.favorites:
    if st.sidebar.button("Remove from Favorites"):
        st.session_state.favorites.remove(city)
        st.rerun()

# Other sidebar options
show_5day = st.sidebar.checkbox("Show 5-Day Forecast", True)
show_hourly = st.sidebar.checkbox("Show Hourly Forecast (24h)", False)
show_alerts = st.sidebar.checkbox("Show Weather Alerts", False)

# Historical weather date input
st.sidebar.subheader(" Weather")
hist_date = st.sidebar.date_input(
    "Select Date (past 7 days max):",
    value=date.today() - timedelta(days=1),
    min_value=date.today() - timedelta(days=7),
    max_value=date.today() - timedelta(days=1)
)

# Theme selection
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])

# Background styling
bg_color = "#ebff0ea4" if theme == "Light" else "#1e1e2f"
text_color = "black" if theme == "Light" else "white"
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    </style>
""", unsafe_allow_html=True)

# Play background sound
def play_sound(condition):
    audio = None
    if "rain" in condition.lower():
        audio = "rain.mp3"
    elif "sun" in condition.lower() or "clear" in condition.lower():
        audio = "birds.mp3"

    if audio and Path(audio).exists():
        st.markdown(f"""
        <audio autoplay loop>
            <source src="{audio}" type="audio/mpeg">
        </audio>
        """, unsafe_allow_html=True)

# Get current weather
def get_current_weather(city):
    url = f"{BASE_URL}/current.json?key={API_KEY}&q={city}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

# Get forecast (including hourly)
def get_forecast(city, days=5):
    url = f"{BASE_URL}/forecast.json?key={API_KEY}&q={city}&days={days}&aqi=no&alerts=yes"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

# Get historical weather
def get_historical_weather(city, date):
    date_str = date.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/history.json?key={API_KEY}&q={city}&dt={date_str}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

# Plot temperature graph for 5-day forecast
def plot_temperature_graph(forecast_data):
    dates = []
    max_temps = []
    min_temps = []

    for day in forecast_data['forecast']['forecastday']:
        dates.append(day['date'])
        max_temps.append(day['day']['maxtemp_c'])
        min_temps.append(day['day']['mintemp_c'])

    if theme == "Dark":
        font_color = "white"
        max_line_color = "lightcoral"
        min_line_color = "lightblue"
        bg_color = "#1e1e2f"
        grid_color = "#444"
    else:
        font_color = "black"
        max_line_color = "firebrick"
        min_line_color = "royalblue"
        bg_color = "white"
        grid_color = "#ddd"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=max_temps, mode='lines+markers', name='Max Temp (°C)',
                             line=dict(color=max_line_color)))
    fig.add_trace(go.Scatter(x=dates, y=min_temps, mode='lines+markers', name='Min Temp (°C)',
                             line=dict(color=min_line_color)))

    fig.update_layout(
        title=dict(text='5-Day Temperature Forecast', font=dict(color=font_color, size=20)),
        xaxis=dict(title='Date', color=font_color, gridcolor=grid_color),
        yaxis=dict(title='Temperature (°C)', color=font_color, gridcolor=grid_color),
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        font=dict(color=font_color),
        legend=dict(font=dict(color=font_color))
    )

    st.plotly_chart(fig, use_container_width=True)

# Main app logic
if city:
    current = get_current_weather(city)
    forecast_data = get_forecast(city, days=5)
    historical = get_historical_weather(city, hist_date)

    if current and forecast_data:
        st.markdown(f"<h1 style='text-align:center;'>🌤️ Weather in {city.title()}</h1>", unsafe_allow_html=True)

        current_condition = current['current']['condition']['text']
        play_sound(current_condition)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.image("http:" + current['current']['condition']['icon'], width=100)
        with col2:
            st.markdown(f"### {current_condition}")
            st.markdown(f"**Temperature:** {current['current']['temp_c']} °C")
            st.markdown(f"**Feels like:** {current['current']['feelslike_c']} °C")
            st.markdown(f"**Humidity:** {current['current']['humidity']}%")
            st.markdown(f"**Wind speed:** {current['current']['wind_kph']} km/h")

        st.markdown("---")

        if show_hourly:
            st.subheader("Hourly Forecast (Next 24h)")
            hours = forecast_data['forecast']['forecastday'][0]['hour']
            cols = st.columns(8)
            for i in range(0, 24, 3):
                hour = hours[i]
                with cols[i//3]:
                    st.markdown(f"**{hour['time'].split()[1]}**")
                    st.image("http:" + hour['condition']['icon'], width=50)
                    st.markdown(f"{hour['temp_c']} °C")
                    st.markdown(hour['condition']['text'])
            st.markdown("---")

        if show_5day:
            st.subheader("5-Day Forecast")
            for day in forecast_data['forecast']['forecastday']:
                st.markdown(f"### {day['date']}")
                cols = st.columns(3)
                with cols[0]:
                    st.image("http:" + day['day']['condition']['icon'], width=75)
                with cols[1]:
                    st.markdown(f"**Condition:** {day['day']['condition']['text']}")
                with cols[2]:
                    st.markdown(f"**Max Temp:** {day['day']['maxtemp_c']} °C")
                    st.markdown(f"**Min Temp:** {day['day']['mintemp_c']} °C")

            plot_temperature_graph(forecast_data)

        if show_alerts:
            alerts = forecast_data.get("alerts", {}).get("alert", [])
            if alerts:
                st.markdown("## ⚠️ Weather Alerts")
                seen = set()
                for alert in alerts:
                    headline = alert.get('headline', '')
                    if headline in seen:
                        continue
                    seen.add(headline)
                    st.markdown(f"### {headline}")
                    st.markdown(f"**Severity:** {alert.get('severity', 'N/A')}")
                    st.markdown(f"**Effective:** {alert.get('effective', 'N/A')}")
                    st.markdown(f"**Expires:** {alert.get('expires', 'N/A')}")
                    st.markdown(f"**Details:** {alert.get('desc', 'N/A')}")
                    st.markdown(f"**Instructions:** {alert.get('instruction', 'N/A')}")
                    st.markdown("---")
            else:
                st.info("No active weather alerts.")

        # Show historical weather summary
        if historical:
            st.markdown("---")
            st.subheader(f" Weather on {hist_date.strftime('%Y-%m-%d')}")
            hist_day = historical.get('forecast', {}).get('forecastday', [{}])[0]
            if hist_day:
                day_data = hist_day.get('day', {})
                st.markdown(f"**Max Temp:** {day_data.get('maxtemp_c', 'N/A')} °C")
                st.markdown(f"**Min Temp:** {day_data.get('mintemp_c', 'N/A')} °C")
                st.markdown(f"**Avg Temp:** {day_data.get('avgtemp_c', 'N/A')} °C")
                st.markdown(f"**Total Precipitation:** {day_data.get('totalprecip_mm', 'N/A')} mm")
                st.markdown(f"**Condition:** {day_data.get('condition', {}).get('text', 'N/A')}")
            else:
                st.info("No historical data found for the selected date.")

    else:
        st.error("City not found or API error. Please check your city or API key.")
else:
    st.info("Please enter a city name in the sidebar.")






