ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONUNBUFFERED 1

# Install build dependencies
# We use 'apk add --no-cache' for Alpine Linux base images, which is common for HA add-ons.
RUN apk add --no-cache python3 py3-pip

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt --break-system-packages

# Copy application code
COPY accuweather_mqtt_publisher.py /app/accuweather_mqtt_publisher.py

# Set working directory inside the container
WORKDIR /app

# Command to run the application
CMD [ "python3", "accuweather_mqtt_publisher.py" ]
