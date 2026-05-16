FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright chromium install
RUN playwright install chromium
RUN playwright install-deps chromium

# App code copy karo
COPY . .

# Port expose karo
EXPOSE 8000

# Default command
CMD ["python", "main.py", "--mode", "dashboard"]