#!/bin/bash

# Ensure the .env file exists
if [ ! -f .env ]; then
  echo "Error: .env file not found! Please create it with the required variables."
  exit 1
fi

# Default port
PORT=8000

# Build the Docker image
echo "Building Docker image..."
docker build -t coin-voyage-api .

# kill current container running on port
docker ps -q --filter "publish=$PORT" | xargs -r docker kill

# Run the Docker container with environment variables from .env
echo "Running Docker container on port $PORT..."
docker run -p $PORT:$PORT --env-file .env coin-voyage-api