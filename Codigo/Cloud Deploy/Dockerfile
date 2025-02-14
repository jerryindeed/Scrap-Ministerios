FROM python:3.9-slim

# Instalar dependencias para Chrome
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    ca-certificates \
    fontconfig \
    libx11-dev \
    libxcomposite1 \
    libxrandr2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libnspr4 \
    libnss3 \
    libgbm-dev \
    libasound2 \
    libxss1 \
    libcurl4 \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb
RUN apt-get install -y -f  # Resolver dependencias

# Instalar ChromeDriver compatible
RUN CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -q "https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia tu código fuente al contenedor
COPY . /app
WORKDIR /app

# Ejecutar el scraper
CMD ["python", "main.py"]
