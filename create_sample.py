#!/usr/bin/env python3
"""
Create a small sample file for testing before full processing
"""

import pandas as pd
import sys

# Load full dataset
input_file = 'data/june01_to_sept25.parquet'
sample_1_file = 'data/sample_1_row.parquet'
sample_2_file = 'data/sample_2_row.parquet'
sample_50_file = 'data/sample_50_rows.parquet'

try:
    df = pd.read_parquet(input_file)
    print(f"Loaded {len(df)} rows from {input_file}")
    
    # Create 1-row sample for local testing
    sample_1 = df.head(1)
    sample_1.to_parquet(sample_1_file, index=False)
    print(f"\n✅ Created 1-row sample: {sample_1_file}")
    print("   Use for: Quick local API validation")
    # Create 2-row sample for local testing
    sample_2 = df.head(2)
    sample_2.to_parquet(sample_2_file, index=False)
    print(f"\n✅ Created 2-row sample: {sample_2_file}")
    print("   Use for: Quick local API validation")
    
    # Create 50-row sample for Datacrunch testing
    sample_50 = df.head(50)
    sample_50.to_parquet(sample_50_file, index=False)
    print(f"\n✅ Created 50-row sample: {sample_50_file}")
    print("   Use for: Datacrunch GPU testing before full run")
    
    print("\n📋 Testing workflow:")
    print("1. Test locally (1 row):")
    print(f"   INPUT_FILE={sample_1_file} python3 process_parquet.py")
    print("\n2. Test on Datacrunch (50 rows):")
    print(f"   scp {sample_50_file} root@INSTANCE_IP:/root/writereader-experiment/data/")
    print(f"   INPUT_FILE={sample_50_file} python3 process_parquet.py")
    print("\n3. If both pass → Full run:")
    print("   python3 process_parquet.py")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
