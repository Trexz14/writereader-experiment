# Writereader AI Equivalence Experiment

**Simple deployment package for processing 13,390 Danish text pairs with AI score capture.**

## 🎯 What This Does

Processes Danish student texts through AI pipeline to collect:
- ✅ **AI confidence scores** (previously missing)
- ✅ **AI text proposals** (always captured)  
- ✅ **Teacher corrections** (when available)
- ✅ **Complete experiment data** for equivalence analysis

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/YOUR_USERNAME/writereader-experiment.git
cd writereader-experiment
./deploy.sh

# 2. Results will be in ./output/
```

## 📊 What You Get

```json
{
  "original_child_text": "Student text",
  "original_adult_text": "Teacher correction", 
  "gdpr_proposed_text": "AI proposal",
  "raw_proposed_text": "AI proposal",
  "ai_score": 1.057,
  "is_proposed": false
}
```

## 🔧 Manual Setup

If you prefer step-by-step:

```bash
# Start services
docker-compose up -d

# Wait for initialization (2-3 minutes)
# Test: curl http://localhost:5002/api/text_to_score/ -d '{"texts":[{"pageId":1,"childText":"test","adultText":"better test"}]}' -H "Content-Type: application/json"

# Process data  
python process_parquet.py

# Results in ./output/processed_results.json
```

## 💡 Key Features

- **Fixed API**: Now returns `aiScore` in responses
- **Complete Data**: Captures both AI proposals AND teacher corrections
- **GPU Ready**: Optimized for 100x speed improvement
- **Proven Setup**: Uses tested components from working deployment

## 📋 Requirements

- Docker + nvidia-docker
- 20GB+ GPU memory (recommended)
- 5GB disk space