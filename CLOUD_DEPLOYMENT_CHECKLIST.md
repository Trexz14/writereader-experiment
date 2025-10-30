# Cloud Deployment Checklist

**Date:** October 30, 2025

## Pre-Deployment (Local)

### 1. Docker Images
- [ ] Build `frederikjwritereader/atel:experiment` (linux/amd64)
- [ ] Build `frederikjwritereader/automaticscore:experiment` (linux/amd64)
- [ ] Push both images to Docker Hub
- [ ] Verify images exist: `docker pull frederikjwritereader/atel:experiment`

### 2. Files Ready
- [ ] `docker-compose.yml` (GPU configuration active)
- [ ] `process_parquet.py`
- [ ] `utils.py`
- [ ] `requirements.txt`
- [ ] `datacrunch-startup.sh`
- [ ] `june01_to_sept25.parquet` (data file)

### 3. Google Drive Models
- [ ] Verify `new_modeldir_v4_atel.zip` exists in My Drive
- [ ] Verify `automaticscoring_models_v2.zip` exists in My Drive
- [ ] Have `rclone.conf` backed up locally at `~/.config/rclone/rclone.conf`

---

## Deployment (Cloud Instance)

### 1. Provision Instance
- [ ] Create Datacrunch instance with:
  - GPU (NVIDIA)
  - CUDA pre-installed
  - Docker pre-installed
  - Sufficient storage (~30GB for models + data)

### 2. Initial Setup
```bash
# SSH into instance
ssh root@<INSTANCE_IP>

# Run startup script
bash <(curl -s https://raw.githubusercontent.com/Trexz14/writereader-experiment/main/datacrunch-startup.sh)
```

### 3. Copy rclone Configuration
**On local machine:**
```bash
ssh root@<INSTANCE_IP> "mkdir -p /root/.config/rclone/"
scp ~/.config/rclone/rclone.conf root@<INSTANCE_IP>:/root/.config/rclone/
```

### 4. Download Models
**On cloud instance:**
```bash
cd /root/writereader-experiment/models

# Preview zip structure first
rclone ls gdrive:new_modeldir_v4_atel.zip
rclone ls gdrive:automaticscoring_models_v2.zip

# Download models
rclone copy gdrive:new_modeldir_v4_atel.zip . --progress
rclone copy gdrive:automaticscoring_models_v2.zip . --progress

# Preview before extracting
unzip -l new_modeldir_v4_atel.zip
unzip -l automaticscoring_models_v2.zip

# Extract
unzip new_modeldir_v4_atel.zip
unzip automaticscoring_models_v2.zip

# Verify structure
ls -la
# Should see: new_modeldirv4_atel/ and autoscoring_v2/
```

### 5. Upload Dataset
**On local machine:**
```bash
scp /Users/frederikjonsson/Desktop/Writereader/Repositories/writereader-experiment/data/june01_to_sept25.parquet \
    root@<INSTANCE_IP>:/root/writereader-experiment/data/
```

### 6. Start Services
**On cloud instance:**
```bash
cd /root/writereader-experiment

# Pull Docker images
docker compose pull

# Start services
docker compose up -d

# Check status
docker compose ps

# Watch logs (wait for models to load)
docker compose logs -f wr-ml-service
# Wait for: "Loading checkpoint shards: 100%"
# Ctrl+C to exit logs
```

### 7. Test API
```bash
# Quick test
curl -X POST http://localhost:5002/api/text_to_score/ \
  -H "Content-Type: application/json" \
  -d '{"texts":[{"pageId":1,"childText":"test","adultText":"test text"}]}'

# Should return JSON with aiScore field
```

### 8. Run Processing
```bash
cd /root/writereader-experiment

# Run batch processing
python3 process_parquet.py \
  --input data/june01_to_sept25.parquet \
  --output output/processed_results.parquet \
  --api-url http://localhost:5002/api/text_to_score/ \
  --batch-size 100

# Monitor progress (will show progress bar)
```

### 9. Download Results
**On local machine (while processing or after completion):**
```bash
# Download results
scp root@<INSTANCE_IP>:/root/writereader-experiment/output/processed_results.parquet ./

# Download failed batches (if any)
scp root@<INSTANCE_IP>:/root/writereader-experiment/output/processed_results_failed_batches.json ./
```

### 10. Cleanup
```bash
# Stop services
docker compose down

# Exit SSH
exit

# Delete Datacrunch instance from dashboard
# IMPORTANT: Don't forget to delete to avoid charges!
```

---

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker compose logs

# Check specific service
docker compose logs wr-ml-service
docker compose logs automaticscore

# Restart services
docker compose down
docker compose up -d
```

### Model Loading Issues
```bash
# Verify model directory structure
ls -la /root/writereader-experiment/models/new_modeldirv4_atel/
ls -la /root/writereader-experiment/models/autoscoring_v2/

# Check environment variables
docker compose config
```

### GPU Not Detected
```bash
# Check GPU
nvidia-smi

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu20.04 nvidia-smi
```

### API Timeout
- Increase timeout in process_parquet.py if needed
- Check if models are fully loaded
- Verify GPU is being used (check nvidia-smi during processing)

---

## Expected Performance

- **GPU Processing:** ~0.5-2 seconds per row
- **Total Time (13,390 rows):** ~2-7 hours
- **Output File:** Should have `aiScore` field for each row
- **Success Rate:** Aim for >95% (some rows may fail validation)

---

## Post-Processing

After downloading results:
```bash
# Check output file
python3 -c "import pandas as pd; df = pd.read_parquet('processed_results.parquet'); print(df.head()); print(f'Total rows: {len(df)}')"

# Verify aiScore column exists
python3 -c "import pandas as pd; df = pd.read_parquet('processed_results.parquet'); print('aiScore' in df.columns)"
```

---

*Remember: Delete the instance when done to avoid unnecessary charges!*
