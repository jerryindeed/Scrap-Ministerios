# Usa una imagen base ligera con Python
FROM python:3.9-slim

# Instala dependencias del sistema necesarias para Chrome y ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    fontconfig \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libglib2.0-0 \
    libnss3 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libxshmfence1 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Descargar e instalar Google Chrome
# Descargar el archivo de Chrome
RUN wget https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.98/linux64/chrome-linux64.zip && \
    ls -l && \  
    unzip chrome-linux64.zip && \
    ls -l && \  
    mv chrome-linux64 /opt/google/chrome && \
    ls -l /opt/google/chrome && \ 
    rm chrome-linux64.zip

# Establecer la variable de entorno para Google Chrome
ENV PATH="/opt/google/chrome:${PATH}"

# Instalar ChromeDriver compatible con la versión de Chrome
RUN CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE_133) && \
    wget -q "https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.98/linux64/chromedriver-linux64.zip" && \
    unzip chromedriver-linux64.zip -d /usr/local/bin/ && \
    rm chromedriver-linux64.zip

# Establecer Chrome como el navegador predeterminado para Selenium
ENV GOOGLE_CHROME_BIN="/opt/google/chrome/chrome"

# Establecer variables de entorno para Selenium
ENV DISPLAY=:99

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias e instalar paquetes de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Definir comando de inicio
CMD ["python", "main.py"]
