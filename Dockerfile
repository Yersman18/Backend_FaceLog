# Use a stable Debian 'Bullseye' version of the Python runtime
FROM python:3.10-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies, including python3-dlib
# This should work on Bullseye
RUN apt-get update && apt-get install -y build-essential cmake python3-dlib

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# dlib will be skipped because it's already installed at the system level
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code to the working directory
COPY . .
