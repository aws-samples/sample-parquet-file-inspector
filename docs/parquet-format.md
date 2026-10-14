# Apache Parquet Format Reference

> **⚠️ Educational use only.** This reference accompanies a tool built for education
> and demonstration purposes, **not for production use**.

A quick reference for understanding what the inspector shows you.

## File Layout

```
┌──────────────────────────────────┐
│  Magic: "PAR1" (4 bytes)         │  ← File header
├──────────────────────────────────┤
│  Row Group 0                     │
│  ├── Column Chunk: col_a         │
│  │   ├── [Dictionary Page]       │
│  │   ├── Data Page 0             │
│  │   └── Data Page 1             │
│  ├── Column Chunk: col_b         │
│  │   ├── Data Page 0             │
│  │   └── Data Page 1             │
│  └── ...                         │
├──────────────────────────────────┤
│  Row Group 1                     │
│  └── ...                         │
├──────────────────────────────────┤
│  Footer (Thrift-encoded)         │  ← File metadata
│  ├── Schema                      │
│  ├── Row Group metadata          │
│  │   └── Column chunk metadata   │
│  │       ├── Encodings           │
│  │       ├── Compression codec   │
│  │       ├── Statistics          │
│  │       └── Page offsets        │
│  └── Key-Value metadata          │
├──────────────────────────────────┤
│  Footer length (4 bytes, LE)     │
│  Magic: "PAR1" (4 bytes)         │  ← File trailer
└──────────────────────────────────┘
```

## Encodings

| Encoding | Description | Best For |
|----------|-------------|----------|
| **PLAIN** | Raw values, no encoding | Fallback; dictionary page values |
| **RLE** | Run-Length Encoding + bit-packing | Definition/repetition levels; boolean columns |
| **RLE_DICTIONARY** | Dictionary indices encoded with RLE | Low-cardinality columns (strings, enums) |
| **PLAIN_DICTIONARY** | Legacy dictionary encoding (deprecated) | Same as RLE_DICTIONARY (older writers) |
| **DELTA_BINARY_PACKED** | Delta + zigzag + bit-packing | Sorted/sequential integers, timestamps |
| **DELTA_LENGTH_BYTE_ARRAY** | Delta-encoded lengths + raw bytes | Variable-length strings |
| **DELTA_BYTE_ARRAY** | Prefix + suffix delta encoding | Sorted strings with common prefixes |
| **BYTE_STREAM_SPLIT** | IEEE754 byte-plane split | Float/double columns (better compression) |

### Common Encoding Combinations

When you see **PLAIN + RLE + RLE_DICTIONARY** on a column, it means:
- **PLAIN** → the dictionary page stores distinct values in plain encoding
- **RLE_DICTIONARY** → data pages store integer indices into the dictionary
- **RLE** → definition levels (null markers) use RLE encoding

This is the standard pattern for dictionary-encoded columns.

## Compression Codecs

| Codec | Ratio | Speed | Notes |
|-------|-------|-------|-------|
| UNCOMPRESSED | 1x | Fastest | No CPU cost |
| SNAPPY | 1.5-2x | Fast | Default in many tools; good balance |
| GZIP | 2-3x | Slow | Better ratio, higher CPU |
| ZSTD | 2-3x | Fast | Best balance of ratio + speed |
| LZ4 | 1.5-2x | Fastest | Minimal CPU overhead |
| BROTLI | 2-4x | Slow | Best ratio, highest CPU |

## Statistics

Column chunk statistics enable **predicate pushdown** (skipping entire row groups):

| Statistic | Purpose |
|-----------|---------|
| `min` / `max` | Range filter: skip row group if query range doesn't overlap |
| `null_count` | Skip if `WHERE col IS NOT NULL` and all values are null |
| `distinct_count` | Cardinality estimation for query planning |

## Key-Value Metadata

Common keys found in the file-level metadata:

| Key | Written By | Contains |
|-----|-----------|----------|
| `pandas` | PyArrow/pandas | JSON: column dtypes, index columns, pandas version |
| `ARROW:schema` | Any Arrow writer | Binary: serialized Arrow IPC schema |
| `org.apache.spark.sql.parquet.row.metadata` | Spark | JSON: Spark schema |
| `parquet.avro.schema` | Avro tools | JSON: Avro schema |
| `geo` | GeoParquet | JSON: CRS, geometry columns, bbox |
| `iceberg.schema` | Apache Iceberg | JSON: Iceberg table schema |

## Physical Types

| Type | Size | Notes |
|------|------|-------|
| BOOLEAN | 1 bit | Bit-packed |
| INT32 | 4 bytes | Also used for DATE, TIME_MILLIS via logical types |
| INT64 | 8 bytes | Also used for TIMESTAMP via logical types |
| INT96 | 12 bytes | Legacy timestamp (deprecated) |
| FLOAT | 4 bytes | IEEE 754 single-precision |
| DOUBLE | 8 bytes | IEEE 754 double-precision |
| BYTE_ARRAY | Variable | Strings, binary, JSON |
| FIXED_LEN_BYTE_ARRAY | Fixed N | UUID, DECIMAL, INTERVAL |

## Repetition Types

| Level | Meaning |
|-------|---------|
| REQUIRED | Never null; no definition level stored |
| OPTIONAL | May be null; 1-bit definition level per value |
| REPEATED | List element; uses repetition + definition levels |

## Further Reading

- [Parquet Format Specification](https://parquet.apache.org/documentation/latest/)
- [Parquet Thrift Definition](https://github.com/apache/parquet-format/blob/master/src/main/thrift/parquet.thrift)
- [DuckDB Parquet Documentation](https://duckdb.org/docs/data/parquet/overview)
