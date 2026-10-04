from flask import Flask, render_template
import requests
import csv
import os
import time
import threading
from datetime import datetime

app = Flask(__name__)

# =====================================================
# BLYNK SETTINGS
# =====================================================

BLYNK_AUTH_TOKEN = "zcITQH0V8qWfCYPFBR1k2mT06t0Lurk0"
BLYNK_URL = "https://blynk.cloud/external/api/get"

CSV_FILE = "greenhouse_data.csv"


# =====================================================
# GET VALUE FROM BLYNK
# =====================================================

def get_value(pin):
    try:
        response = requests.get(
            BLYNK_URL,
            params={
                "token": BLYNK_AUTH_TOKEN,
                "V": pin
            },
            timeout=10
        )

        if response.status_code == 200:
            return response.text.strip()

        return "ERROR"

    except:
        return "ERROR"


# =====================================================
# READ ALL GREENHOUSE DATA
# =====================================================

def read_greenhouse():

    temperature = get_value(3)
    humidity = get_value(4)
    soil = get_value(5)
    light = get_value(6)
    water = get_value(7)
    pump = get_value(2)
    mode = get_value(0)

    return {
        "temperature": temperature,
        "humidity": humidity,
        "soil": soil,
        "light": light,
        "water": water,
        "pump": pump,
        "mode": mode
    }


# =====================================================
# SMART RECOMMENDATION ENGINE
# =====================================================

def get_recommendation(data):

    suggestions = []

    try:
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        soil = float(data["soil"])
        light = float(data["light"])
        water = float(data["water"])

        # Temperature
        if temperature > 30:
            suggestions.append(
                "🌡️ Temperature is high. Improve greenhouse ventilation or cooling."
            )

        elif temperature < 18:
            suggestions.append(
                "🌡️ Temperature is low. Protect the plants from excessive cold."
            )

        # Humidity
        if humidity > 80:
            suggestions.append(
                "💧 Humidity is high. Improve ventilation to reduce excess moisture."
            )

        elif humidity < 40:
            suggestions.append(
                "💧 Humidity is low. Consider increasing moisture around the plants."
            )

        # Soil
        if soil < 30:
            if water < 20:
                suggestions.append(
                    "🌱 Soil is dry and water level is low. Refill the water tank."
                )
            else:
                suggestions.append(
                    "🌱 Soil moisture is low. Irrigation is recommended."
                )

        elif soil < 40:
            suggestions.append(
                "🌱 Soil moisture is moderate. Monitor the soil condition."
            )

        else:
            suggestions.append(
                "🌱 Soil moisture is sufficient."
            )

        # Water
        if water < 20:
            suggestions.append(
                "🚰 Water level is critically low. Please refill the tank."
            )

        elif water < 40:
            suggestions.append(
                "🚰 Water level is getting low. Consider refilling the tank."
            )

        # Light
        if light < 100:
            suggestions.append(
                "☀️ Light intensity is low. Check whether the plants receive enough light."
            )

        # If everything is normal
        if not suggestions:
            return "✅ Greenhouse conditions are normal. Plants are in a healthy monitored range."

        return " | ".join(suggestions)

    except:
        return "⚠️ Waiting for valid sensor data..."


# =====================================================
# CREATE CSV FILE
# =====================================================

def create_csv():

    if not os.path.exists(CSV_FILE):

        with open(CSV_FILE, "w", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                "Date",
                "Time",
                "Temperature",
                "Humidity",
                "Soil Moisture",
                "Light Intensity",
                "Water Level",
                "Pump Status",
                "Mode"
            ])


# =====================================================
# SAVE DATA TO CSV
# =====================================================

def save_data():

    data = read_greenhouse()

    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    with open(CSV_FILE, "a", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            date,
            current_time,
            data["temperature"],
            data["humidity"],
            data["soil"],
            data["light"],
            data["water"],
            data["pump"],
            data["mode"]
        ])

    print("-----------------------------------")
    print("Time          :", current_time)
    print("Temperature   :", data["temperature"], "°C")
    print("Humidity      :", data["humidity"], "%")
    print("Soil Moisture :", data["soil"], "%")
    print("Light         :", data["light"], "lux")
    print("Water Level   :", data["water"], "%")
    print("Pump          :", "ON" if data["pump"] == "1" else "OFF")
    print("Mode          :", "MANUAL" if data["mode"] == "1" else "AUTO")
    print("Data saved ✓")
    print("-----------------------------------")


# =====================================================
# BACKGROUND DATA LOGGER
# =====================================================

def data_logger():

    create_csv()

    while True:

        try:
            save_data()

        except Exception as e:
            print("Logger error:", e)

        time.sleep(10)


# =====================================================
# WEBSITE
# =====================================================

@app.route("/")
def dashboard():

    data = read_greenhouse()

    data["pump"] = "ON" if data["pump"] == "1" else "OFF"
    data["mode"] = "MANUAL" if data["mode"] == "1" else "AUTO"

    data["suggestion"] = get_recommendation(data)

    return render_template(
        "index.html",
        data=data
    )


# =====================================================
# START APPLICATION
# =====================================================

if __name__ == "__main__":

    print("===================================")
    print("🌱 SMART GREENHOUSE WEB DASHBOARD")
    print("===================================")

    # Start CSV logger in background
    logger_thread = threading.Thread(
        target=data_logger,
        daemon=True
    )

    logger_thread.start()

    # Start website
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )