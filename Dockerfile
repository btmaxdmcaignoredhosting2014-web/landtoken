FROM selenium/standalone-chrome:latest

USER root
WORKDIR /app

# Install Python & pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    ln -s /usr/bin/python3 /usr/bin/python

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 10000

# Run as non-root user (security best practice)
USER seluser

# Start command
CMD ["python3", "app.py"]
