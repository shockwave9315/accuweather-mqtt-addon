FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Zainstaluj podstawowe narzędzia i zależności
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Skopiuj plik z wymaganiami i zainstaluj zależności Pythona
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Skopiuj kod źródłowy aplikacji
COPY accuweather_mqtt_publisher.py .

# Uruchom aplikację
CMD ["python", "accuweather_mqtt_publisher.py"]
