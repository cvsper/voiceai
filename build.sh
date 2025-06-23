#!/bin/bash
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Node.js dependencies..."
cd demo
npm ci --production=false

echo "Building React frontend..."
npm run build

echo "Build completed successfully!"