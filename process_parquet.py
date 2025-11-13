#!/usr/bin/env python3
"""
Batch processing script for parquet data through automaticscore API
Designed for Datacrunch deployment with Docker

USAGE:
    python3 process_parquet.py --input <input_file> --output <output_file> --api-url <api_url> --batch-size <size>

INPUT:
    - Parquet file with columns: ChildText, AdultText, Time, ID
    - Example: data/sample_2_row.parquet

OUTPUT:
    - Parquet file with original columns plus API response fields:
        - pageId: Row index
        - gdpr: {childText, adultText, proposedText} - GDPR-cleaned texts
        - isProposed: Boolean indicating if text was proposed
        - raw: {childText, adultText, proposedText} - Raw unprocessed texts
        - aiScore: Float confidence score from AI model (CRITICAL FIELD)
        - processed_at: Timestamp
        - batch_number: Batch identifier
    - Failed batches JSON file (if any failures occur)

EXAMPLE:
    python3 process_parquet.py \
        --input data/sample_2_row.parquet \
        --output output/test_results.parquet \
        --api-url http://localhost:5002/api/text_to_score/ \
        --batch-size 2
"""

import pandas as pd
import requests
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import time
from tqdm import tqdm
from utils import make_api_call, save_results, setup_logging

def load_parquet_data(file_path: str) -> pd.DataFrame:
    """Load parquet file and validate structure"""
    try:
        df = pd.read_parquet(file_path)
        print(f"Loaded {len(df)} rows from {file_path}")
        
        # Validate required columns
        required_cols = ['ChildText', 'AdultText', 'Time', 'ID']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        print(f"Data columns: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"Error loading parquet file: {e}")
        sys.exit(1)

def prepare_api_batch(df_batch: pd.DataFrame) -> dict:
    """Convert DataFrame batch to API format, filtering out empty rows"""
    texts = []
    skipped = []
    
    for i, row in df_batch.iterrows():
        # Check if ChildText or AdultText is empty/whitespace after stripping
        child_text = str(row['ChildText']).strip()
        adult_text = str(row['AdultText']).strip()
        
        if not child_text or not adult_text:
            # Skip empty rows - they cause Status 400 errors
            skipped.append({
                'index': i,
                'id': row.get('ID', 'unknown'),
                'reason': 'empty_text'
            })
            continue
        
        texts.append({
            "pageId": i,  # Use row index as integer pageId
            "childText": child_text,
            "adultText": adult_text
        })
    
    return {"texts": texts, "skipped": skipped}

def process_parquet_file(input_file: str, output_file: str, 
                        api_url: str, batch_size: int = 100):
    """Main processing function"""
    
    # Load data
    df = load_parquet_data(input_file)
    
    # Prepare results storage
    results = []
    failed_batches = []
    skipped_rows = []  # Track all skipped rows
    
    # Process in batches
    total_batches = len(df) // batch_size + (1 if len(df) % batch_size > 0 else 0)
    
    print(f"Processing {len(df)} rows in {total_batches} batches of {batch_size}")
    
    with tqdm(total=len(df), desc="Processing rows") as pbar:
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            try:
                # Prepare API request (filters out empty rows)
                api_request = prepare_api_batch(batch_df)
                
                # Track skipped rows from this batch
                if api_request.get('skipped'):
                    skipped_rows.extend(api_request['skipped'])
                    print(f"Batch {batch_num}: Skipped {len(api_request['skipped'])} empty row(s)")
                
                # Only make API call if we have texts to process
                if api_request['texts']:
                    # Make API call
                    response = make_api_call(api_url, {"texts": api_request['texts']})
                    
                    if response and 'texts' in response:
                        # FIX: Match results by pageId, not by index position
                        # The API may return fewer results than sent (filtering), so we can't use enumerate
                        for result in response['texts']:
                            page_id = result.get('pageId')
                            
                            # Find the original row by matching the pageId (which is the pandas index)
                            try:
                                original_row = batch_df.loc[page_id]
                            except KeyError:
                                print(f"Warning: Result pageId {page_id} not found in batch {batch_num}")
                                continue
                            
                            combined_result = {
                                # Original data (from parquet file)
                                'original_id': original_row['ID'],
                                'original_child_text': original_row['ChildText'],
                                'original_adult_text': original_row['AdultText'],
                                'original_time': original_row['Time'],
                                
                                # API results
                                'page_id': page_id,
                                'is_proposed': result.get('isProposed', False),
                                'ai_score': result.get('aiScore'),  # AI confidence score
                                
                                # GDPR cleaned results
                                'gdpr_child_text': result.get('gdpr', {}).get('childText'),
                                'gdpr_adult_text': result.get('gdpr', {}).get('adultText'),
                                'gdpr_proposed_text': result.get('gdpr', {}).get('proposedText'),
                                
                                # Raw proposed text (no original equivalent)
                                'raw_proposed_text': result.get('raw', {}).get('proposedText'),
                                
                                # Processing metadata
                                'processed_at': datetime.now().isoformat(),
                                'batch_number': batch_num
                            }
                            results.append(combined_result)
                    else:
                        print(f"Warning: No valid response for batch {batch_num}")
                        failed_batches.append(batch_num)
                    
            except Exception as e:
                print(f"Error processing batch {batch_num}: {e}")
                failed_batches.append(batch_num)
                
            pbar.update(len(batch_df))
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
    
    # Save results
    save_results(results, output_file, failed_batches, skipped_rows)
    
    print(f"\nProcessing complete!")
    print(f"Successfully processed: {len(results)} rows")
    print(f"Skipped (empty text): {len(skipped_rows)} rows")
    print(f"Failed batches: {len(failed_batches)}")
    print(f"Results saved to: {output_file}")

def main():
    """Main entry point"""
    setup_logging()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process parquet data through automaticscore API')
    parser.add_argument('--input', type=str, 
                       default=os.getenv('INPUT_FILE', 'data/june01_to_sept25.parquet'),
                       help='Input parquet file path')
    parser.add_argument('--output', type=str,
                       default=os.getenv('OUTPUT_FILE', 'output/processed_results.parquet'),
                       help='Output parquet file path')
    parser.add_argument('--api-url', type=str,
                       default=os.getenv('AUTOMATICSCORE_URL', 'http://localhost:5002/api/text_to_score/'),
                       help='API endpoint URL')
    parser.add_argument('--batch-size', type=int,
                       default=int(os.getenv('BATCH_SIZE', '100')),
                       help='Batch size for processing')
    
    args = parser.parse_args()
    
    input_file = args.input
    output_file = args.output
    api_url = args.api_url
    batch_size = args.batch_size
    
    print(f"Configuration:")
    print(f"  Input file: {input_file}")
    print(f"  Output file: {output_file}")
    print(f"  API URL: {api_url}")
    print(f"  Batch size: {batch_size}")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found!")
        sys.exit(1)
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Process the file
    process_parquet_file(input_file, output_file, api_url, batch_size)

if __name__ == "__main__":
    main()