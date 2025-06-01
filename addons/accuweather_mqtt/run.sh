#!/usr/bin/env bash
set -e

# Wczytaj konfigurację z Home Assistant
CONFIG_PATH="/data/options.json"

export ACCUWEATHER_API_KEY=$(jq -r '.ACCUWEATHER_API_KEY' "$CONFIG_PATH")
export ACCUWEATHER_CITY_NAME=$(jq -r '.ACCUWEATHER_CITY_NAME' "$CONFIG_PATH")
export ACCUWEATHER_LOCATION_KEY=$(jq -r '.ACCUWEATHER_LOCATION_KEY' "$CONFIG_PATH")
export MQTT_BROKER_ADDRESS=$(jq -r '.MQTT_BROKER_ADDRESS' "$CONFIG_PATH")
export MQTT_BROKER_PORT=$(jq -r '.MQTT_BROKER_PORT' "$CONFIG_PATH")
export MQTT_USERNAME=$(jq -r '.MQTT_USERNAME' "$CONFIG_PATH")
export MQTT_PASSWORD=$(jq -r '.MQTT_PASSWORD' "$CONFIG_PATH")
export REFRESH_INTERVAL_SECONDS=$(jq -r '.REFRESH_INTERVAL_SECONDS' "$CONFIG_PATH")

echo "[INFO] Starting AccuWeather MQTT Publisher..."
exec python3 /app/accuweather_mqtt_publisher.py
