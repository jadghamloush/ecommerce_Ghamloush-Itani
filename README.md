Certainly! Below is a comprehensive `README.md` file for your project. This README includes all necessary sections to guide your professor through building, running, and testing your containerized applications.

---

# E-commerce Microservices Project

## Project Overview

This project implements an e-commerce platform using a microservices architecture. It consists of four services, each responsible for a specific domain in the application:

1. **Customer Service (Service 1)**: Manages customer information.
2. **Inventory Service (Service 2)**: Manages goods and inventory.
3. **Sales Service (Service 3)**: Handles sales transactions.
4. **Reviews Service (Service 4)**: Manages product reviews.

Each service is packaged into its own Docker container, including all dependencies, to ensure consistent and efficient deployment across various environments.

## Prerequisites

To build and run this project, you need to have the following software installed:

- **Docker**: Version 20.10 or higher
- **Python**: Version 3.7 or higher

## Installation Instructions

### Cloning the Repository

Clone the project repository to your local machine:

```bash
git clone https://github.com/yourusername/ecommerce_project.git
cd ecommerce_project
```

## Building the Docker Images

You can build each service individually:

```bash
# Build Service 1 Image
cd service1
docker build -t service1-image .

# Build Service 2 Image
cd ../service2
docker build -t service2-image .

# Build Service 3 Image
cd ../service3
docker build -t service3-image .

# Build Service 4 Image
cd ../service4
docker build -t service4-image .
```

## Running the Services

Run each service in its own container:

```bash
# Run Service 1 Container
docker run -d -p 5000:5000 --name service1-container service1-image

# Run Service 2 Container
docker run -d -p 5001:5001 --name service2-container service2-image

# Run Service 3 Container
docker run -d -p 5002:5002 --name service3-container service3-image

# Run Service 4 Container
docker run -d -p 5003:5003 --name service4-container service4-image
```

### Running Automated Tests

To run the Pytest test suites for each service:

1. **Install Pytest** (if not already installed):

   ```bash
   pip install pytest
   ```

2. **Run Tests for Each Service**:

   ```bash
   # Service 1 Tests
   cd service1
   pytest test_service1.py

   # Service 2 Tests
   cd ../service2
   pytest test_service2.py

   # Service 3 Tests
   cd ../service3
   pytest test_service3.py

   # Service 4 Tests
   cd ../service4
   pytest test_service4.py
   ```

## Stopping the Services

```bash
docker stop service1-container
docker rm service1-container

docker stop service2-container
docker rm service2-container

docker stop service3-container
docker rm service3-container

docker stop service4-container
docker rm service4-container
```
