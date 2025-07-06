# SPIKE-PERF-002: Serialization Format Benchmarks

## Summary
This spike compares the performance of common Python serialization formats. Each
format was evaluated for encoded size and time to serialize and deserialize a
sample payload.

## Method
A small benchmark script (`experiments/performance/serialization_bench.py`)
serializes a list of 1000 dictionaries using `pickle`, `json`, `msgpack`, and
`protobuf`. The script measures the byte size of the encoded payload and the
execution time for 1000 serialization and deserialization loops.

Compression with gzip and lzma was tested on the msgpack output to gauge the
effect on size and throughput.

## Results
The table below shows the relative performance observed on a development
workstation. Times are the total seconds for 1000 iterations.

| Format    | Size (bytes) | Serialize | Deserialize |
|-----------|-------------:|----------:|------------:|
| pickle    | 27367        | 0.0342s   | 0.0328s     |
| json      | 24000        | 0.0523s   | 0.0657s     |
| msgpack   | 20983        | 0.0331s   | 0.0310s     |
| protobuf  | 22019        | 0.0465s   | 0.0402s     |

Compression reduced the msgpack payload to ~7500 bytes with gzip and ~6800 bytes
with lzma, but both methods roughly doubled encode and decode times.

## Observations
- `msgpack` produced the smallest payload and near‑pickle performance.
- `json` was slower to process but only slightly larger without compression.
- `protobuf` offered strong typing at the cost of additional overhead.
- Gzip or lzma compression can shrink payloads dramatically, though throughput
  suffers. Compression is worthwhile only when network costs dominate.

