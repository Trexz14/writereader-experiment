#!/bin/bash
# Datacrunch Startup Script for Writereader AI Equivalence Experiment
# This script runs automatically when the instance starts

set -e

echo "Starting Writereader Experiment Setup..."

# Update system
apt-get update

# Install additional tools if needed
apt-get install -y git curl wget htop unzip

# Install rclone for Google Drive access
curl https://rclone.org/install.sh | bash

# Verify GPU and Docker
echo "Checking GPU..."
nvidia-smi

echo "Checking Docker..."
docker --version
docker-compose --version

# Test Docker GPU support
echo "Testing Docker GPU support..."
docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu20.04 nvidia-smi

# Create workspace
cd /root
echo "Setting up workspace..."

# Clone or update the experiment repository
if [ ! -d "writereader-experiment" ]; then
    echo "Cloning experiment repository..."
    git clone https://github.com/Trexz14/writereader-experiment.git
    cd writereader-experiment
else
    echo "Repository exists, pulling latest changes..."
    cd writereader-experiment
    git pull origin main
fi

# Create necessary directories
mkdir -p data output models

echo "Basic setup complete!"
echo ""
echo "Manual steps still needed:"
echo "1. Copy rclone config: scp ~/.rclone.conf root@YOUR_IP:/root/.rclone.conf"
echo "2. Download models from Google Drive using rclone"
echo "3. Upload data file: scp data/june01_to_sept25.parquet root@YOUR_IP:/root/writereader-experiment/data/"
echo "4. Start services: docker-compose up -d"
echo "5. Wait for model loading: docker-compose logs -f"
echo "6. Run processing: python3 process_parquet.py"
echo ""
echo "Remember to destroy this instance when done to save costs!"
echo ""
echo "Ready for your AI equivalence experiment!"