#!/usr/bin/env python3
"""
Generate a sample IoT sensor Parquet file for the Parquet File Inspector demo.

This script creates a ~18MB Parquet file with:
  - 500,000 rows of synthetic IoT sensor readings
  - 10 columns with varied types (string, timestamp, float, int, double)
  - 5 row groups (100,000 rows each)
  - Snappy compression
  - Dictionary encoding on low-cardinality string columns
  - Column statistics enabled
  - ~2% null values in the temperature column

The generated file exercises multiple Parquet features:
  - Dictionary encoding (device_id, status, firmware_version)
  - Plain encoding (latitude, longitude, temperature, humidity)
  - RLE for definition levels (nullable columns)
  - Multiple row groups for row-group-level inspection
  - Column statistics (min/max/null_count) for predicate pushdown demo

Requirements:
  pip install pyarrow numpy

Usage:
  python3 generate_sample_data.py [output_path]

Output:
  sample-data/iot_sensors.parquet (default)
"""

import os
import sys
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timedelta

# Configuration
NUM_ROWS = 500_000
ROW_GROUP_SIZE = 100_000  # 5 row groups
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sample-data')
OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUTPUT_DIR, 'iot_sensors.parquet')

# Reproducible random state
np.random.seed(42)


def generate():
    """Generate the sample Parquet file."""
    print(f"Generating {NUM_ROWS:,} rows of IoT sensor data...")

    # --- Column: device_id (STRING, dictionary-encoded) ---
    # 50 unique devices - low cardinality triggers dictionary encoding
    devices = [f"sensor-{i:04d}" for i in range(50)]
    device_ids = np.random.choice(devices, NUM_ROWS)

    # --- Column: timestamp (TIMESTAMP[us]) ---
    # Continuous timestamps over 7 days - good for delta encoding
    base_time = datetime(2026, 7, 1, 0, 0, 0)
    timestamps = [base_time + timedelta(seconds=i * 1.2) for i in range(NUM_ROWS)]

    # --- Column: temperature_celsius (FLOAT32, nullable) ---
    # Normal distribution with 2% null rate to demonstrate null handling
    temperature = np.random.normal(22.5, 5.0, NUM_ROWS).astype(np.float32)
    temp_mask = np.random.random(NUM_ROWS) < 0.02  # 2% nulls

    # --- Column: humidity_percent (FLOAT32) ---
    humidity = np.clip(np.random.normal(55.0, 15.0, NUM_ROWS), 0, 100).astype(np.float32)

    # --- Column: pressure_hpa (INT32) ---
    # Narrow range - good for RLE/delta encoding
    pressure = np.random.randint(995, 1025, NUM_ROWS).astype(np.int32)

    # --- Column: battery_level (FLOAT32) ---
    battery = np.clip(np.random.uniform(0.1, 1.0, NUM_ROWS), 0, 1).astype(np.float32)

    # --- Column: status (STRING, dictionary-encoded) ---
    # 5 distinct values - highly compressible with dictionary encoding
    statuses = ["OK", "WARN", "ERROR", "MAINTENANCE", "OFFLINE"]
    status = np.random.choice(statuses, NUM_ROWS, p=[0.85, 0.08, 0.03, 0.02, 0.02])

    # --- Column: latitude (FLOAT64) ---
    lat = np.random.uniform(31.0, 33.5, NUM_ROWS)

    # --- Column: longitude (FLOAT64) ---
    lon = np.random.uniform(34.0, 36.0, NUM_ROWS)

    # --- Column: firmware_version (STRING, dictionary-encoded) ---
    firmware_versions = ["v2.1.0", "v2.1.1", "v2.2.0-beta", "v3.0.0", "v2.0.9"]
    firmware = np.random.choice(firmware_versions, NUM_ROWS)

    # Build Arrow table
    temp_array = pa.array(temperature.tolist(), mask=temp_mask.tolist(), type=pa.float32())

    table = pa.table({
        'device_id': pa.array(device_ids, type=pa.string()),
        'timestamp': pa.array(timestamps, type=pa.timestamp('us')),
        'temperature_celsius': temp_array,
        'humidity_percent': pa.array(humidity.tolist(), type=pa.float32()),
        'pressure_hpa': pa.array(pressure.tolist(), type=pa.int32()),
        'battery_level': pa.array(battery.tolist(), type=pa.float32()),
        'status': pa.array(status.tolist(), type=pa.string()),
        'latitude': pa.array(lat.tolist(), type=pa.float64()),
        'longitude': pa.array(lon.tolist(), type=pa.float64()),
        'firmware_version': pa.array(firmware.tolist(), type=pa.string()),
    })

    # Write with multiple row groups, snappy compression, and dictionary encoding
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    pq.write_table(
        table,
        OUTPUT_FILE,
        row_group_size=ROW_GROUP_SIZE,
        compression='snappy',
        use_dictionary=['device_id', 'status', 'firmware_version'],
        write_statistics=True,
    )

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"✅ Generated: {OUTPUT_FILE}")
    print(f"   Size: {size_mb:.1f} MB")
    print(f"   Rows: {NUM_ROWS:,}")
    print(f"   Row groups: {NUM_ROWS // ROW_GROUP_SIZE}")
    print(f"   Columns: {table.num_columns}")
    print(f"   Schema:")
    for field in table.schema:
        print(f"     - {field.name}: {field.type}")


if __name__ == '__main__':
    generate()
