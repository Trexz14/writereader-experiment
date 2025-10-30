#!/bin/bash
# Datacrunch Startup Script for Writereader AI Equivalence Experiment
# This script runs automatically when the instance starts

set -e

echo "Starting Writereader Experiment Setup..."

# Update system
apt-get update

# Install additional tools if needed
apt-get install -y git git-lfs curl wget htop unzip

# Install rclone for Google Drive access
curl https://rclone.org/install.sh | bash || true

# Verify GPU and Docker
echo "Checking GPU and docker"
nvidia-smi

docker --version
docker compose version

# Test Docker GPU support
echo "Testing Docker GPU support..."
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu20.04 nvidia-smi

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

echo "--- AUTOMATED SETUP COMPLETE ---"
echo ""
echo "The environment is ready. Please perform the following manual steps:"
# echo "1. Copy rclone config: scp ~/.config/rclone/rclone.conf root@YOUR_IP:/root/.config/rclone/"
# echo "2. Download models: rclone copy 'gdrive:Writereader/Equivalence_Experiment/models' './models' --progress"
# echo "3. Upload data file: scp /path/to/your/data.parquet root@YOUR_IP:/root/writereader-experiment/data/"
# echo "4. Pull images and start services: docker compose pull && docker compose up -d"
# echo "5. Wait for model loading: docker compose logs -f wr-ml-service-1"
# echo "6. Run processing: INPUT_FILE='data/your_data.parquet' BATCH_SIZE='100' python3 process_parquet.py"
# echo ""
# echo "Remember to destroy this instance when done to save costs!"
# echo ""
# echo "Ready for your AI equivalence experiment!"
# echo ""
echo "=== STEP 1: Upload service code to build Docker images ==="
echo "On your local machine, run:"
echo "  scp -r /Users/frederikjonsson/Desktop/Writereader/Repositories/wr-ml-service root@YOUR_IP:/root/"
echo "  scp -r /Users/frederikjonsson/Desktop/Writereader/Repositories/automaticscore root@YOUR_IP:/root/"
echo ""
echo "=== STEP 2: Build and push Docker images ==="
echo "On this server, run:"
echo "  cd /root/wr-ml-service/app && docker build -t frederikjwritereader/atel:experiment . && docker push frederikjwritereader/atel:experiment"
echo "  cd /root/automaticscore/app && docker build -t frederikjwritereader/automaticscore:experiment . && docker push frederikjwritereader/automaticscore:experiment"
echo ""
echo "=== STEP 3: Setup models and data ==="
echo "  mkdir -p /root/.config/rclone/"
echo "  scp ~/.config/rclone/rclone.conf root@YOUR_IP:/root/.config/rclone/"
echo "  cd /root/writereader-experiment/models"
echo "  rclone copy gdrive:new_modeldir_v4_atel.zip . --progress"
echo "  rclone copy gdrive:automaticscoring_models_v2.zip . --progress"
echo "  unzip new_modeldir_v4_atel.zip"
echo "  unzip automaticscoring_models_v2.zip"
echo "  scp /path/to/june01_to_sept25.parquet root@YOUR_IP:/root/writereader-experiment/data/"
echo ""
echo "=== STEP 4: Run services ==="
echo "  cd /root/writereader-experiment"
echo "  docker compose pull"
echo "  docker compose up -d"
echo "  docker compose logs -f"
echo ""
echo "=== STEP 5: Process data ==="
echo "  python3 process_parquet.py --input data/june01_to_sept25.parquet --output output/processed_results.parquet --api-url http://localhost:5002/api/text_to_score/ --batch-size 100"
echo ""
echo "Remember to destroy this instance when done to save costs!"