#!/bin/bash
# Tag your working images for the experiment

echo "🏷️  Tagging experiment images..."

# Tag your working experiment images
docker tag automaticscore-experiment:latest writereader/automaticscore:experiment
docker tag atel:latest writereader/atel:experiment

echo "✅ Images tagged:"
echo "   writereader/automaticscore:experiment (with AI score fix)"
echo "   writereader/atel:experiment"

echo ""
echo "💡 Next steps:"
echo "   1. Push to Docker Hub: docker push writereader/automaticscore:experiment"
echo "   2. Copy models and data to experiment directory"
echo "   3. Run ./deploy.sh"