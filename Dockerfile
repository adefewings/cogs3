# Parent image
FROM python:3.13

# Install additional software packages
RUN apt-get update && apt-get install -y vim
RUN pip install --upgrade pip

# Prevent Python from writing out pyc files
ENV PYTHONDONTWRITEBYTECODE 1

# Enable log messages to be immediately sent to the output stream
ENV PYTHONUNBUFFERED 1

# Create a directory to store the application's source code
RUN mkdir /app

# Set the working directory
WORKDIR /app

# Install the required software packages
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy the application's source code to the working directory
COPY . /app/

# Install geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz
RUN tar -xzf geckodriver-v0.26.0-linux64.tar.gz
RUN chmod +x geckodriver
RUN mv geckodriver /usr/local/bin
RUN rm geckodriver-v0.26.0-linux64.tar.gz

# Need firefox & a few other bits for geckodriver
RUN apt-get update 
RUN apt-get install -y firefox-esr \
    libdbus-glib-1-2 \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libxrender1 \
    libfontconfig1 \
    libx11-xcb1 \
    libxcomposite1 \
    libasound2 \
    libxdamage1 \
    libxrandr2 \
    libgbm-dev \
    libxtst6 \
    libnss3 \
    libxss1 \
    libxcb-shm0 \
    libxcb1 \
    libglib2.0-0 \
    libgl1 \
    libgl1-mesa-dri \
    libgbm1 \
    libpci3 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    xvfb \
    wget

# Chromium alternative
# Install Chromium and Chromedriver dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Symlink for Selenium compatibility
RUN ln -s /usr/bin/chromium /usr/bin/google-chrome

# Create a directory to store emails
RUN mkdir -vp /tmp/app-messages
