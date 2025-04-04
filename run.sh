#!/bin/bash

echo "Stopping and removing existing container..."
docker stop f39a9dd013d9
docker rm f39a9dd013d9

echo "Building new image..."
docker build -t my-flask-app .

echo "Starting container in background..."
docker run -d -p 5000:5000 --name objective_clarke my-flask-app

echo "Done!"