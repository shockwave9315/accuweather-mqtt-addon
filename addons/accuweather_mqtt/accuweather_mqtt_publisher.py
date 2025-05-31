import requests
import json
import time
import paho.mqtt.client as mqtt
import os # Importujemy moduł os do odczytu zmiennych środowiskowych

# --- KONFIGURACJA (ODCZYT Z ZMIENNYCH ŚRODOWISKOWYCH ADD-ONU) ---
# Klucz API AccuWeather (będzie przekazany z config.json Add-onu)
ACCUWEATHER_API_KEY = os.environ.get("ACCUWEATHER_API_KEY")

# Lokalizacja do pobierania pogody
ACCUWEATHER_CITY_NAME = os.environ.get("ACCUWEATHER_CITY_NAME", "Tarnów") # Domyślna wartość, jeśli nie ustawiono
ACCUWEATHER_LOCATION_KEY = os.environ.get("ACCUWEATHER_LOCATION_KEY", "")

# Konfiguracja MQTT
MQTT_BROKER_ADDRESS = os.environ.get("MQTT_BROKER_ADDRESS")
MQTT_BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", 1883)) # Upewnij się, że port to int
MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
MQTT_CLIENT_ID = "accuweather_publisher" # Może być stały, albo też zmienna środowiskowa

# Interwał odświeżania danych w sekundach (będzie przekazany z config.json Add-onu)
REFRESH_INTERVAL_SECONDS = int(os.environ.get("REFRESH_INTERVAL_SECONDS", 300))

# --- Funkcje AccuWeather API ---

def get_location_key(city_name):
    """
    Pobiera Location Key dla danego miasta z AccuWeather API.
    """
    search_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {
        'apikey': ACCUWEATHER_API_KEY,
        'q': city_name,
        'language': 'pl-pl',
        'details': 'false'
    }
    try:
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json()
        if results:
            print(f"Znaleziono ID miasta '{city_name}': {results[0]['Key']}")
            return results[0]['Key']
        else:
            print(f"Błąd: Nie znaleziono klucza lokalizacji dla '{city_name}'.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Błąd API podczas wyszukiwania klucza dla '{city_name}': {e}")
        return None

def get_current_conditions(location_key):
    """
    Pobiera aktualne warunki pogodowe dla danego Location Key z AccuWeather API.
    """
    conditions_url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
    params = {
        'apikey': ACCUWEATHER_API_KEY,
        'language': 'pl-pl',
        'details': 'false'
    }
    try:
        response = requests.get(conditions_url, params=params, timeout=10)
        response.raise_for_status()
        conditions = response.json()
        if conditions and isinstance(conditions, list) and len(conditions) > 0:
            temp_c = conditions[0]['Temperature']['Metric']['Value']
            phrase = conditions[0]['WeatherText']
            is_day_time = conditions[0]['IsDayTime']
            return temp_c, phrase, is_day_time
        else:
            print(f"Błąd: Nie uzyskano danych pogodowych dla Location Key: {location_key}")
            return None, None, None
    except requests.exceptions.RequestException as e:
        print(f"Błąd API podczas pobierania warunków dla {location_key}: {e}")
        return None, None, None


# --- Funkcje MQTT ---

def on_connect(client, userdata, flags, rc):
    """Callback wywoływany po połączeniu z brokerem MQTT."""
    if rc == 0:
        print("Połączono z brokerem MQTT!")
    else:
        print(f"Nie udało się połączyć z brokerem MQTT. Kod błędu: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback wywoływany po rozłączeniu z brokerem MQTT."""
    print(f"Rozłączono z brokerem MQTT z kodem: {rc}")

def publish_discovery_config(client, component_type, entity_name, unique_id_suffix, state_topic_suffix, device_class=None, unit_of_measurement=None, value_template=None, payload_on=None, payload_off=None):
    """Publikuje wiadomość konfiguracyjną MQTT Discovery dla pojedynczego sensora."""
    
    # Base ID dla urządzenia (wszystkie sensory z tego skryptu będą należeć do tego "urządzenia")
    device_name = "AccuWeather Weather"
    device_id = "accuweather_weather_publisher"
    
    # Zmieniamy temat konfiguracji w zależności od component_type
    config_topic = f"homeassistant/{component_type}/{device_id}/{unique_id_suffix}/config"
    
    payload = {
        "name": entity_name,
        # Niezależny temat dla wartości (używamy tego samego dla wszystkich typów, co jest ok)
        "state_topic": f"home/accuweather/{state_topic_suffix}",
        "unique_id": f"{device_id}_{unique_id_suffix}",
        "force_update": True, # Zawsze wysyłaj aktualizacje, nawet jeśli wartość się nie zmieniła
        "device": { # Definicja urządzenia, do którego należy sensor
            "identifiers": [device_id],
            "name": device_name,
            "manufacturer": "AccuWeather",
            "model": "MQTT Publisher"
        }
    }

    if unit_of_measurement:
        payload["unit_of_measurement"] = unit_of_measurement
    if device_class:
        payload["device_class"] = device_class
    if value_template:
        payload["value_template"] = value_template
    
    # Specyficzne dla binary_sensor: payload_on i payload_off
    if payload_on is not None:
        payload["payload_on"] = payload_on
    if payload_off is not None:
        payload["payload_off"] = payload_off

    client.publish(config_topic, json.dumps(payload), qos=0, retain=True)
    print(f"Opublikowano MQTT Discovery config dla '{entity_name}' ({component_type}) na temacie: {config_topic}")
    # Retain=True sprawia, że broker zachowuje tę wiadomość i wysyła ją do nowych subskrybentów (np. HA po restarcie)

def publish_mqtt_data(client, topic_suffix, value):
    """Publikuje rzeczywiste dane sensora."""
    state_topic = f"home/accuweather/{topic_suffix}"
    client.publish(state_topic, str(value), qos=0, retain=False)
    print(f"Opublikowano dane '{value}' na temacie: {state_topic}")


# --- Główna logika programu ---

def main():
    global ACCUWEATHER_LOCATION_KEY

    # Sprawdzenie, czy wszystkie niezbędne zmienne środowiskowe są ustawione
    if not ACCUWEATHER_API_KEY:
        print("Błąd: ACCUWEATHER_API_KEY nie jest ustawiony w konfiguracji Add-onu!")
        return
    if not MQTT_BROKER_ADDRESS or not MQTT_USERNAME or not MQTT_PASSWORD:
        print("Błąd: Konfiguracja MQTT (adres brokera, nazwa użytkownika lub hasło) nie jest ustawiona w Add-onie!")
        return

    # Sprawdź, czy Location Key jest już ustawiony, jeśli nie, wyszukaj go
    if not ACCUWEATHER_LOCATION_KEY:
        print(f"Wyszukiwanie Location Key dla '{ACCUWEATHER_CITY_NAME}'...")
        ACCUWEATHER_LOCATION_KEY = get_location_key(ACCUWEATHER_CITY_NAME)
        if not ACCUWEATHER_LOCATION_KEY:
            print("Nie można kontynuować bez Location Key. Sprawdź nazwę miasta lub klucz API.")
            return

    # Inicjalizacja klienta MQTT
    client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, 60)
        client.loop_start() # Uruchom pętlę w tle do obsługi połączenia i ponownych połączeń

        # Opublikuj konfigurację Discovery raz na początku
        # Sensory: Temperatura, Warunki
        publish_discovery_config(
            client,
            "sensor", # Typ komponentu w HA
            "AccuWeather Temperature",
            "temperature",
            "temperature",
            device_class="temperature",
            unit_of_measurement="°C"
        )
        publish_discovery_config(
            client,
            "sensor", # Typ komponentu w HA
            "AccuWeather Conditions",
            "conditions",
            "conditions",
            device_class="enum"
        )
        
        # Zmieniona konfiguracja dla binary_sensora
        publish_discovery_config(
            client,
            "binary_sensor", # KLUCZOWA ZMIANA: To jest binary_sensor!
            "AccuWeather Is Day Time",
            "is_day_time",
            "is_day_time",
            device_class="light", # Klasa urządzenia, np. light, occupancy
            payload_on="on",     # Wartość, która oznacza 'włączony' stan
            payload_off="off"    # Wartość, która oznacza 'wyłączony' stan
        )
        
        # Główna pętla programu
        while True:
            print("\nPobieram aktualne warunki pogodowe...")
            temp_c, phrase, is_day_time = get_current_conditions(ACCUWEATHER_LOCATION_KEY)

            if temp_c is not None and phrase is not None and is_day_time is not None:
                print(f"Pobrane dane: Temp: {temp_c}°C, Warunki: {phrase}, Dzień: {is_day_time}")
                publish_mqtt_data(client, "temperature", temp_c)
                publish_mqtt_data(client, "conditions", phrase)
                # Dla binary_sensorów Home Assistant oczekuje 'on' lub 'off'
                publish_mqtt_data(client, "is_day_time", "on" if is_day_time else "off")
            else:
                print("Nie udało się pobrać danych pogodowych. Spróbuję ponownie.")

            print(f"Czekam {REFRESH_INTERVAL_SECONDS} sekund do następnego odświeżenia...")
            time.sleep(REFRESH_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nProgram zakończony przez użytkownika.")
    except Exception as e:
        print(f"Wystąpił krytyczny błąd: {e}")
    finally:
        if 'client' in locals() and client.is_connected():
            client.loop_stop() # Zatrzymaj pętlę MQTT
            client.disconnect() # Rozłącz się z brokerem


if __name__ == "__main__":
    main()