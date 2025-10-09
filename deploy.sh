#!/bin/bash
set -e

echo "🚀 Writereader AI Equivalence Experiment Deployment"
echo "=================================================="

# Check GPU
echo "🔍 Checking GPU..."
if ! nvidia-smi > /dev/null 2>&1; then
    echo "❌ No GPU detected. This will be slow on CPU."
    read -p "Continue? (y/N) " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# Create directories
echo "📁 Setting up directories..."
mkdir -p data output models

# Download data (placeholder - update with your actual data source)
echo "📊 Setting up data..."
if [ ! -f "data/june01_to_sept25.parquet" ]; then
    echo "❗ Please place your data file at: data/june01_to_sept25.parquet"
    echo "   You can copy it from your local workspace"
fi

# Download models (placeholder - update with your actual model source)  
echo "🤖 Setting up models..."
if [ ! -d "models/modeldir_v1" ] || [ ! -d "models/autoscoring_v2" ]; then
    echo "❗ Please copy model directories to:"
    echo "   - models/modeldir_v1/"
    echo "   - models/autoscoring_v2/"
    echo "   You can copy them from your local workspace"
fi

# Tag local images (if running locally)
echo "🏷️  Tagging Docker images..."
if docker images | grep -q "automaticscore-experiment"; then
    docker tag automaticscore-experiment:latest writereader/automaticscore:experiment
fi
if docker images | grep -q "atel"; then
    docker tag atel:latest writereader/atel:experiment
fi

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# Health check
echo "🔍 Health check..."
for i in {1..10}; do
    if curl -s http://localhost:5002/api/text_to_score/ > /dev/null 2>&1; then
        echo "✅ Services are ready!"
        break
    fi
    echo "   Attempt $i/10 - waiting..."
    sleep 10
done

# Process data
echo "🔄 Starting data processing..."
if [ -f "data/june01_to_sept25.parquet" ]; then
    python process_parquet.py
    echo "✅ Processing complete! Check output/ directory"
else
    echo "❗ Data file not found. Please add data/june01_to_sept25.parquet and run:"
    echo "   python process_parquet.py"
fi

echo ""
echo "🎉 Deployment complete!"
echo "📊 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"