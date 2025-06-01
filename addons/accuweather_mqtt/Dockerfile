ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONUNBUFFERED 1

# Dodatkowe pakiety potrzebne do budowania i instalacji Pythona/pip na Alpine
# Często brakuje tych pakietów, co powoduje błąd "exit code: 255"
RUN \
    if [ -f /etc/alpine-release ]; then \
        apk update && apk add --no-cache \
            build-base \
            python3-dev \
            py3-pip \
            libffi-dev \
            openssl-dev \
            bzip2-dev \
            zlib-dev \
            readline-dev \
            sqlite-dev \
            libressl-dev \
            libxml2-dev \
            libxslt-dev \
            gcc \
            musl-dev \
            curl \
            wget \
            git || \
        echo "Failed to install some Alpine dev packages, continuing..."; \
    elif [ -f /etc/debian_version ]; then \
        apt-get update && apt-get install -y --no-install-recommends \
            python3 \
            python3-pip \
            build-essential \
            libffi-dev \
            libssl-dev \
            curl \
            wget \
            git && \
        rm -rf /var/lib/apt/lists/*; \
    else \
        echo "Unsupported base OS for direct package installation. Assuming build tools are available."; \
    fi

# Upewnij się, że pip jest aktualny i dostępny (używaj python3 -m pip)
RUN python3 -m ensurepip --upgrade || \
    (wget -qO /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py && \
     python3 /tmp/get-pip.py --no-cache-dir && \
     rm /tmp/get-pip.py) || \
    echo "pip installation/upgrade failed, continuing..."; \
    python3 -m pip install --no-cache-dir --upgrade pip

# Copy and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt --break-system-packages

# Copy application code
COPY accuweather_mqtt_publisher.py /app/accuweather_mqtt_publisher.py

# Set working directory inside the container
WORKDIR /app

# Command to run the application
CMD [ "python3", "accuweather_mqtt_publisher.py" ]
