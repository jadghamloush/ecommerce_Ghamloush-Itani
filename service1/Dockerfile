# Use the official Python image from Docker Hub
FROM python:3.8-alpine

# Set the working directory
WORKDIR /app

# Copy the service code into the container
COPY service1.py /app/service1.py

# Install dependencies
RUN pip install flask flask_cors

# Expose port 5000 (or the port your service runs on)
EXPOSE 5000

COPY . /app

# Command to run the application
CMD ["python", "service1.py"]
