FROM selenium/standalone-chrome:latest

USER root
WORKDIR /app

# Python + pip install
RUN apt-get update && apt-get install -y python3-pip

# Dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# App code
COPY . .

# Port
EXPOSE 10000

# Run
CMD ["python3", "app.py"]
