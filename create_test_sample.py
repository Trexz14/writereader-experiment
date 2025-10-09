#!/usr/bin/env python3
"""
Create a custom test parquet file with specific text pair
"""

import pandas as pd
from datetime import datetime
import uuid

# Create test data with specific text pair that should result in is_proposed: false
# (good adult text that corrects a simple typo)
test_data = {
    'ID': [str(uuid.uuid4())],
    'ChildText': ['Dette er en god tesst.'],  # Has typo: "tesst" instead of "test"
    'AdultText': ['Dette er en god test.'],   # Good correction, should NOT trigger proposal
    'Time': [datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]]
}

# Create DataFrame
df = pd.DataFrame(test_data)

# Save as parquet
output_file = 'data/june01_to_sept25_single_sample.parquet'
df.to_parquet(output_file, index=False)

print(f"Created test parquet file: {output_file}")
print(f"Data:")
print(df.to_string(index=False))