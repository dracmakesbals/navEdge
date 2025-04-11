import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

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

        # Wait for and select both input boxes by their shared class
        input_boxes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='combobox']//input")))

        # Enter pickup location
        input_boxes[0].send_keys(pickup)
        input_boxes[0].send_keys(Keys.RETURN)
        time.sleep(2)

        # Enter drop location
        input_boxes[1].send_keys(drop)
        input_boxes[1].send_keys(Keys.RETURN)

        # Wait for directions to load
        time.sleep(2)

        # ETA and distance
        eta_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'MespJc')]")))
        distance_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'ivN21e')]")))

        eta_full_text = eta_elem.text
        # Search for the "X min" pattern anywhere in the text
        match = re.search(r"(\d+\s*min)", eta_full_text)

        if match:
            eta = match.group(1)
            # Everything after 'min' (i.e., after match.end())
            route_info = eta_full_text[match.end():].strip()
            # Remove the word 'Details' from the end if present
            route_info = re.sub(r"\bDetails\b\.?", "", route_info, flags=re.IGNORECASE).strip()
        else:
            eta = eta_full_text
            route_info = ""

        distance = distance_elem.text
        return eta, distance , route_info

    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None, None

    finally:
        driver.quit()

# Streamlit UI
st.set_page_config(page_title="ETA & Distance Checker", layout="centered")
st.title("MyPickup ETA & Distance Checker")

pickup = st.text_input("Enter Pickup Location")
drop = st.text_input("Enter Drop Location")

if st.button("Get ETA and Distance"):
    if pickup and drop:
        with st.spinner("Fetching data..."):
            eta, distance , route_info = get_eta_distance(pickup, drop)
            if eta and distance and route_info:
                st.success(f"🕒 ETA: {eta}")
                st.info(f"📍 Distance: {distance}")
                st.info(f"🎯 Route Info: {route_info}")
            else:
                st.warning("⚠️ Could not fetch data. Please check the input or try again.")
    else:
        st.warning("Please enter both Pickup and Drop locations.")
