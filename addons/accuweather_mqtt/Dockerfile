ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONUNBUFFERED 1

# Upewnij się, że Python i pip są dostępne. Obrazy bazowe Home Assistant często mają je już zainstalowane
# lub wymagają specyficznej metody instalacji, jeśli brakuje.
# Ta instrukcja jest bardziej odporna i często stosowana w dodatkach HA.
RUN \
    if [ -f /etc/alpine-release ]; then \
        apk add --no-cache python3 py3-pip || \
        apk add --no-cache python3-dev python3-pip || \
        echo "Python/pip already installed or alternative installation needed on Alpine"; \
    elif [ -f /etc/debian_version ]; then \
        apt-get update && apt-get install -y python3 python3-pip --no-install-recommends && \
        rm -rf /var/lib/apt/lists/*; \
    else \
        echo "Unsupported base OS for direct Python/pip installation. Assuming Python is available."; \
    fi

# Upgrade pip (to jest dobra praktyka)
RUN pip install --no-cache-dir --upgrade pip

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt --break-system-packages

# Copy application code
COPY accuweather_mqtt_publisher.py /app/accuweather_mqtt_publisher.py

# Set working directory inside the container
WORKDIR /app

# Command to run the application
CMD [ "python3", "accuweather_mqtt_publisher.py" ]
