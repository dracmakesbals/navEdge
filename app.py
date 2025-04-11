import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import pandas as pd
from datetime import datetime

tti_df = pd.read_csv(r"resources/average_travel_time_by_day.csv")

# Function to match input with area/road (case-insensitive) and return TTI
def get_simple_match(user_input, day_input):
    user_input = user_input.lower()
    today_df = tti_df[tti_df['day'] == day_input]

    for _, row in today_df.iterrows():
        area = str(row['Area Name']).lower()
        road = str(row['Road/Intersection Name']).lower()

        if user_input in area or user_input in road:
            return row['Area Name'], row['Road/Intersection Name'], row['Travel Time Index']

    return None, None, 1.0  # Default if no match found

# Function to get ETA and distance from Google Maps using Selenium
def get_eta_distance(pickup, drop):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")

    chromedriver_path = r"resources\chromedriver.exe"
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://www.google.com/maps/dir/")
        wait = WebDriverWait(driver, 2)

        input_boxes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='combobox']//input")))

        input_boxes[0].send_keys(pickup)
        input_boxes[0].send_keys(Keys.RETURN)
        time.sleep(2)

        input_boxes[1].send_keys(drop)
        input_boxes[1].send_keys(Keys.RETURN)
        time.sleep(2)

        eta_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'MespJc')]")))
        distance_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'ivN21e')]")))

        eta_full_text = eta_elem.text
        match = re.search(r"(\d+\s*min)", eta_full_text)

        if match:
            eta = match.group(1)
            route_info = eta_full_text[match.end():].strip()
            route_info = re.sub(r"\bDetails\b\.?", "", route_info, flags=re.IGNORECASE).strip()
        else:
            eta = eta_full_text
            route_info = ""

        distance = distance_elem.text
        return eta, distance, route_info

    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None, None, None

    finally:
        driver.quit()


# Streamlit UI
st.set_page_config(page_title="ETA & Distance Checker", layout="centered")
st.title("MyPickup ETA & Distance Checker")

pickup = st.text_input("Enter Pickup Location")
drop = st.text_input("Enter Drop Location")

# Dropdown for selecting day of the week
day_input = st.selectbox(
    "Select Day of the Week",
    options=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    index=datetime.today().weekday() if datetime.today().weekday() < 7 else 0
)

pickup_hour = st.selectbox(
    "Select Pickup Hour",
    options=[f"{i:02d}" for i in range(24)],
    index=datetime.now().hour
)

traffic_multipliers = {
    "weekday": {
        "00": 1.0, "01": 1.0, "02": 1.0, "03": 1.0, "04": 1.1,
        "05": 1.2, "06": 1.4, "07": 1.7, "08": 2.3, "09": 2.1,
        "10": 1.7, "11": 1.5, "12": 1.6, "13": 1.7, "14": 1.6,
        "15": 1.7, "16": 1.9, "17": 2.2, "18": 2.4, "19": 2.0,
        "20": 1.6, "21": 1.4, "22": 1.2, "23": 1.1
    },
    "weekend": {
        "00": 1.0, "01": 1.0, "02": 1.0, "03": 1.0, "04": 1.0,
        "05": 1.0, "06": 1.1, "07": 1.2, "08": 1.4, "09": 1.6,
        "10": 1.8, "11": 1.9, "12": 2.0, "13": 2.0, "14": 1.9,
        "15": 1.8, "16": 1.8, "17": 1.9, "18": 2.0, "19": 1.9,
        "20": 1.7, "21": 1.5, "22": 1.3, "23": 1.1
    }
}

if st.button("Get ETA and Distance"):
    if pickup and drop:
        with st.spinner("Fetching data..."):
            pickup_area, pickup_road, pickup_tti = get_simple_match(pickup, day_input)
            drop_area, drop_road, drop_tti = get_simple_match(drop, day_input)

            average_tti = round((pickup_tti + drop_tti) / 2, 3)
            # Map user-selected day to weekday/weekend
            day_category = "weekday" if day_input in ["Mon", "Tue", "Wed", "Thu", "Fri"] else "weekend"
            hour_multiplier = traffic_multipliers[day_category].get(pickup_hour, 1.0)
            final_tti = round(average_tti * hour_multiplier, 3)

            eta, distance, route_info = get_eta_distance(pickup, drop)
            eta_minutes = int(re.search(r"\d+", eta).group())

            # Calculate adjusted ETA
            adjusted_eta = round(eta_minutes * final_tti)

            if eta and distance:
                st.success(f"🕒 ETA: {eta}")
                st.info(f"📍 Distance: {distance}")
                st.info(f"🎯 Route Info: {route_info}")
                st.success(f"⏱️ Adjusted ETA (based on day): {adjusted_eta} min")
                st.caption(f"Matched pickup: {pickup_area}, {pickup_road} | drop: {drop_area}, {drop_road}")
            else:
                st.warning("⚠️ Could not fetch data. Please check the input or try again.")
    else:
        st.warning("Please enter both Pickup and Drop locations.")