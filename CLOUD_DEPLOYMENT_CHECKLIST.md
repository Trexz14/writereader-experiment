# Cloud Deployment Checklist

**Last Updated:** November 6, 2025  
**Status:** ✅ Successfully tested with 13,390 row production run

## Quick Start (TL;DR)

For experienced users who have done this before:

```bash
# 1. Provision GPU instance and SSH in
ssh root@<INSTANCE_IP>

# 2. Run startup script
bash <(curl -s https://raw.githubusercontent.com/Trexz14/writereader-experiment/main/datacrunch-startup.sh)

# 3. Copy rclone config (from local machine)
scp ~/.rclone.conf root@<INSTANCE_IP>:/root/.rclone.conf

# 4. Download models and DELETE ZIPs (on instance)
cd /root/writereader-experiment/models
rclone copy gdrive:new_modeldir_v4_atel.zip . --progress
rclone copy gdrive:automaticscoring_models_v2.zip . --progress
unzip new_modeldir_v4_atel.zip
unzip automaticscoring_models_v2.zip
rm *.zip  # ⚠️ CRITICAL - frees 25GB

# 5. Upload data (from local machine)
scp june01_to_sept25.parquet root@<INSTANCE_IP>:/root/writereader-experiment/data/

# 6. Start services (on instance)
cd /root/writereader-experiment
docker compose up -d
docker compose logs -f wr-ml-service  # Wait for model loading

# 7. Test with 2 rows
python3 create_test_sample.py
python3 process_parquet.py --input data/sample_2_row.parquet --output output/test.parquet --api-url http://localhost:5002/api/text_to_score/ --batch-size 2
cat output/test.json | grep ai_score  # Verify field exists

# 8. Run production with nohup
nohup python3 process_parquet.py --input data/june01_to_sept25.parquet --output output/processed_results.parquet --api-url http://localhost:5002/api/text_to_score/ --batch-size 100 > output/processing.log 2>&1 &
tail -f output/processing.log  # Monitor, then disconnect

# 9. Download results (from local machine, after completion)
scp root@<INSTANCE_IP>:~/writereader-experiment/output/processed_results.* ./

# 10. Cleanup
ssh root@<INSTANCE_IP> "cd writereader-experiment && docker compose down"
# Then destroy instance via dashboard
```

---

## ⚠️ CRITICAL WARNINGS

### 1. Disk Space Management
**MUST DELETE ZIP FILES AFTER EXTRACTION**
- Model ZIPs consume 25GB+ and double your disk usage
- After extracting models, immediately run: `cd models && rm *.zip`
- Monitor disk space: `df -h` (keep >20GB free)
- Full disk will crash processing silently

### 2. Process Management
**ALWAYS USE NOHUP FOR LONG-RUNNING PROCESSES**
- SSH connections WILL timeout during 5+ hour runs
- Use: `nohup python3 process_parquet.py ... > output/processing.log 2>&1 &`
- Monitor with: `tail -f output/processing.log`
- Process continues even if you disconnect

### 3. Validation Before Full Run
**TEST WITH 2 ROWS FIRST**
- Always run 2-row test before committing to full dataset
- Verify `aiScore` field exists in output
- Check Docker logs for any warnings
- Confirm GPU is being utilized: `nvidia-smi`

---

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
- [x] Verify `new_modeldir_v4_atel.zip` exists in My Drive (24 GB - confirmed)
- [x] Verify `automaticscoring_models_v2.zip` exists in My Drive (18 KB - confirmed)
- [x] Have `rclone.conf` backed up locally at `~/.rclone.conf` (confirmed working)

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
scp ~/.rclone.conf root@<INSTANCE_IP>:/root/.rclone.conf

# Verify it works
ssh root@<INSTANCE_IP> "rclone ls gdrive: | head -5"
```

### 4. Download and Extract Models
**On cloud instance:**
```bash
cd /root/writereader-experiment/models

# Check available disk space BEFORE downloading
df -h
# Need at least 60GB free (30GB models + 25GB ZIP + 5GB safety margin)

# Download models
rclone copy gdrive:new_modeldir_v4_atel.zip . --progress
rclone copy gdrive:automaticscoring_models_v2.zip . --progress

# Extract models
unzip new_modeldir_v4_atel.zip
# Note: Extracts to modeldir_v1/ NOT new_modeldirv4_atel/
unzip automaticscoring_models_v2.zip

# ⚠️ CRITICAL: DELETE ZIP FILES IMMEDIATELY
rm new_modeldir_v4_atel.zip
rm automaticscoring_models_v2.zip
# This frees 25GB+ of disk space

# Verify structure
ls -la
# Should see: modeldir_v1/ and autoscoring_v2/

# Verify disk space after cleanup
df -h
# Should have ~22GB free (68% usage on 96GB disk)
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

### 7. Test API with 2-Row Sample
```bash
# Create 2-row test sample
cd /root/writereader-experiment
python3 create_test_sample.py

# Run 2-row test to validate everything works
python3 process_parquet.py \
  --input data/sample_2_row.parquet \
  --output output/test_results.parquet \
  --api-url http://localhost:5002/api/text_to_score/ \
  --batch-size 2

# Verify aiScore field exists in output
cat output/test_results.json | grep "ai_score"
# Should see: "ai_score": 1.xxxxx

# ✅ If test passes, proceed to full run
```

### 8. Run Full Processing (Production)
```bash
cd /root/writereader-experiment

# ⚠️ CRITICAL: Use nohup for long-running processes
nohup python3 process_parquet.py \
  --input data/june01_to_sept25.parquet \
  --output output/processed_results.parquet \
  --api-url http://localhost:5002/api/text_to_score/ \
  --batch-size 100 > output/processing.log 2>&1 &

# Get process ID
echo $!

# Monitor progress (Ctrl+C to exit, process continues)
tail -f output/processing.log

# Check if still running after reconnect
ps aux | grep process_parquet

# Expected: ~5-6 hours for 13,390 rows on NVIDIA L40S
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

### Disk Space Full
**Symptoms:** Process dies silently, `journalctl` shows "No space left on device"
```bash
# Check disk usage
df -h

# Find large files
du -h --max-depth=1 /root | sort -hr | head -10
cd ~/writereader-experiment/models
ls -lh

# Solution: Delete ZIP files
rm *.zip

# Verify space freed
df -h
```

### Process Died After SSH Disconnect
**Symptoms:** `ps aux | grep process_parquet` returns nothing after reconnect
**Cause:** Process wasn't started with nohup
**Prevention:** Always use nohup for long-running processes
```bash
# Check if it's really dead
ps aux | grep python

# Restart with nohup
nohup python3 process_parquet.py ... > output/processing.log 2>&1 &
```

### Services Won't Start
```bash
# Check logs
docker compose logs

# Check specific service
docker compose logs wr-ml-service
docker compose logs automaticscore

# Check disk space (common cause)
df -h

# Restart services
docker compose down
docker compose up -d
```

### Model Loading Issues
```bash
# Verify model directory structure
ls -la /root/writereader-experiment/models/modeldir_v1/
ls -la /root/writereader-experiment/models/autoscoring_v2/

# Check volumes are mounted correctly
docker compose config | grep volumes

# Check service logs
docker compose logs wr-ml-service | grep -i "model\|error"
```

### GPU Not Detected
```bash
# Check GPU
nvidia-smi

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu20.04 nvidia-smi

# Check compose file has GPU config
grep -A 5 "deploy:" docker-compose.yml
```

### API Errors (Status 400)
**Symptoms:** Batch fails with "API error (attempt 1): Status 400"
**Cause:** Malformed input data, special characters, or empty fields
**Impact:** ~121 rows lost per failed batch (with batch-size=100)
**Investigation:**
```bash
# Check failed batches
cat output/processed_results_failed_batches.json

# Extract rows from failed batch (e.g., batch 8 = rows 700-799)
python3 -c "
import pandas as pd
df = pd.read_parquet('data/june01_to_sept25.parquet')
batch_num = 8
start = (batch_num - 1) * 100
end = batch_num * 100
print(df.iloc[start:end])
"
```

### API Timeout
**Symptoms:** "Read timed out. (read timeout=600)"
**Cause:** Batch contains unusually long/complex text
**Solution:** Increase timeout or process problematic batches separately
```bash
# Increase timeout in process_parquet.py (line ~50)
# Change: timeout=600 to timeout=1200
```

---

## Expected Performance

**Validated on:** November 6, 2025 with NVIDIA L40S (49GB VRAM)

### Processing Metrics
- **GPU Processing:** 1.0-3.2 seconds per row (avg 1.42s)
- **CPU Processing:** ~6 seconds per row (for comparison)
- **Speedup:** 4x faster on GPU
- **Total Time (13,390 rows):** 5 hours 16 minutes
- **Success Rate:** 88% (11,816/13,390 rows)
- **Failed Batches:** 13 (mostly Status 400 errors, 1 timeout)

### Resource Usage
- **VRAM:** 14.3GB / 49GB (29% utilization)
- **Temperature:** Stable at 37°C
- **Power:** 81W / 350W
- **Disk Space:** 65GB used after cleanup (22GB free)

### Output Files
- `processed_results.parquet` (~2.7MB for 11,816 rows)
- `processed_results.json` (~8.6MB debug format)
- `processed_results_failed_batches.json` (~134 bytes)
- `processing.log` (~15KB with full progress)

### Cost Estimate (Datacrunch GPU)
- **Instance:** NVIDIA L40S (~$1.60/hour)
- **Total Time:** ~8 hours (including setup)
- **Total Cost:** ~$12.80
- **Cost per Row:** $0.0011 per successfully processed row

---

## Performance Optimization Tips

### Increase Batch Size
Current: 100 rows/batch. With 29% VRAM usage, could try:
```bash
# Test with larger batches
--batch-size 200
# or
--batch-size 500
```

### Monitor GPU Utilization
```bash
# Watch GPU in real-time during processing
watch -n 1 nvidia-smi
```

### Reduce Failed Batches
- Add input validation for special characters
- Handle empty/null fields
- Sanitize text encoding before processing
- Implement retry logic with exponential backoff

---

## Post-Processing

After downloading results:
```bash
# Check output file
python3 -c "import pandas as pd; df = pd.read_parquet('processed_results.parquet'); print(df.head()); print(f'Total rows: {len(df)}')"

# Verify aiScore column exists
python3 -c "import pandas as pd; df = pd.read_parquet('processed_results.parquet'); print('aiScore' in df.columns)"

# Check aiScore distribution
python3 -c "import pandas as pd; df = pd.read_parquet('processed_results.parquet'); print(df['ai_score'].describe())"

# Analyze failed batches
cat processed_results_failed_batches.json
```

---

## Quick Reference Commands

### Check Processing Status
```bash
# After reconnecting to instance
ssh root@<INSTANCE_IP>

# Is process still running?
ps aux | grep process_parquet

# View progress
tail -f ~/writereader-experiment/output/processing.log

# Check how many results so far (while running)
cd ~/writereader-experiment/output
ls -lh processed_results.*
# Note: Files only appear after processing completes
```

### Emergency Stop
```bash
# Find process ID
ps aux | grep process_parquet

# Kill process (if needed)
kill <PID>

# Stop Docker services
cd ~/writereader-experiment
docker compose down
```

### Download Everything
```bash
# On local machine - download all output
scp -r root@<INSTANCE_IP>:~/writereader-experiment/output ./cloud_output

# Or download specific files
scp root@<INSTANCE_IP>:~/writereader-experiment/output/processed_results.parquet ./
scp root@<INSTANCE_IP>:~/writereader-experiment/output/processed_results_failed_batches.json ./
scp root@<INSTANCE_IP>:~/writereader-experiment/output/processing.log ./
```

---

## Pre-Flight Checklist Summary

Before starting full processing, verify:
- [ ] Disk space >20GB free (`df -h`)
- [ ] ZIP files deleted from models directory
- [ ] Docker containers running (`docker compose ps`)
- [ ] 2-row test completed successfully
- [ ] `aiScore` field present in test output
- [ ] Using nohup command for production run
- [ ] Monitoring log file shows progress
- [ ] Can disconnect/reconnect without killing process

---

*Last tested successfully: November 6, 2025*  
*Instance: Datacrunch NVIDIA L40S*  
*Dataset: 13,390 rows, 88% success rate*  
*Processing time: 5h 16m*

**Remember: Delete the instance when done to avoid unnecessary charges!**
