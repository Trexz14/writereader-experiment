#!/usr/bin/env python3
"""
Utility functions for parquet processing
"""

import requests
import pandas as pd
import json
import logging
import os
import time
from typing import Dict, Any, List, Optional

def setup_logging():
    """Set up logging configuration"""
    # Use relative path for local testing, absolute for Docker
    log_path = './output/processing.log' if not os.path.exists('/output') else '/output/processing.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

def make_api_call(api_url: str, request_data: Dict[str, Any], 
                  max_retries: int = 1, timeout: int = 600) -> Dict[str, Any]:
    """Make API call with retry logic"""
    
    for attempt in range(max_retries):
        try:
            # Verbose logging (commented out for faster processing)
            # print(f"\n🚀 Making API call (attempt {attempt + 1}/{max_retries})")
            # print(f"📍 URL: {api_url}")
            # print(f"📊 Processing {len(request_data.get('texts', []))} text(s)")
            # print(f"⏰ Timeout: {timeout} seconds")
            # print(f"🔄 Starting request at: {time.strftime('%H:%M:%S')}")
            
            start_time = time.time()
            response = requests.post(
                api_url,
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            )
            end_time = time.time()
            
            # print(f"✅ Response received in {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API error (attempt {attempt + 1}): Status {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        except requests.exceptions.RequestException as e:
            print(f"Request error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    print(f"Failed to get response after {max_retries} attempts")
    return None

def save_results(results: List[Dict], output_file: str, failed_batches: List[int], skipped_rows: Optional[List[Dict]] = None):
    """Save processing results to parquet file"""
    
    if results:
        # Convert to DataFrame and save as parquet
        results_df = pd.DataFrame(results)
        results_df.to_parquet(output_file, index=False)
        print(f"Saved {len(results)} results to {output_file}")
        
        # Also save as JSON for debugging
        json_file = output_file.replace('.parquet', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Debug JSON saved to {json_file}")
    
    # Save failed batches info
    if failed_batches:
        failed_file = output_file.replace('.parquet', '_failed_batches.json')
        with open(failed_file, 'w') as f:
            json.dump({'failed_batches': failed_batches}, f, indent=2)
        print(f"Failed batches info saved to {failed_file}")
    
    # Save skipped rows info
    if skipped_rows:
        skipped_file = output_file.replace('.parquet', '_skipped_rows.json')
        with open(skipped_file, 'w') as f:
            json.dump({'skipped_rows': skipped_rows, 'total_skipped': len(skipped_rows)}, f, indent=2)
        print(f"Skipped rows info saved to {skipped_file}")

def test_api_connection(api_url: str) -> bool:
    """Test if API is accessible"""
    try:
        # Test with a minimal request
        test_data = {
            "texts": [{
                "pageId": 1,
                "childText": "test text", 
                "adultText": "test text"
            }]
        }
        
        response = requests.post(
            api_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ API connection successful: {api_url}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}: {api_url}")
            return False
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False