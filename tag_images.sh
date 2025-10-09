#!/bin/bash
# Tag your working images for the experiment

echo "🏷️  Tagging experiment images..."

# Tag your working experiment images
docker tag automaticscore-experiment:latest frederikjwritereader/automaticscore:experiment
docker tag atel:latest frederikjwritereader/atel:experiment

echo "✅ Images tagged:"
echo "   frederikjwritereader/automaticscore:experiment (with AI score fix)"
echo "   frederikjwritereader/atel:experiment"

echo ""
echo "💡 Next steps:"
echo "   1. Push to Docker Hub: docker push frederikjwritereader/automaticscore:experiment"
echo "   2. Copy models and data to experiment directory"
echo "   3. Run ./deploy.sh"