# Parikshak Operational Benchmarks Report

This report documents measured performance and throughput metrics under live load profiles.

## Throughput Profile
* **Rule Engine Throughput**: 179417.25 reviews/sec (10765035.17 reviews/minute)
* **Sustained Throughput**: 179417.25 reviews/sec
* **Peak Throughput**: 8031.87 reviews/sec (under 100 concurrent workers)

## Concurrency Performance Matrix
| Concurrency Level | Throughput (reviews/sec) | Average Latency (ms) | Min Latency (ms) | Max Latency (ms) | Exceptions Count |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1 User** | 1594.39 | 0.02 | 0.02 | 0.02 | 0 |
| **10 Users** | 6567.71 | 0.03 | 0.01 | 0.14 | 0 |
| **50 Users** | 8014.49 | 0.01 | 0.01 | 0.02 | 0 |
| **100 Users** | 8031.87 | 0.01 | 0.01 | 0.03 | 0 |

## Latency Characterization
* **Single Review Latency**: 0.006 ms
* **Batch Review Latency**: 0.028 ms (5 reviews processed sequentially)
* **Concurrent Review Average Latency (100 users)**: 0.01 ms

## Boot and Startup Gate Timings
* **Cold Start DB Connection Init**: 4.25 ms
* **Warm Start DB Connection Init**: 1.23 ms
* **Startup Safety Gate Integrity Scan**: 0.44 ms

*Verified: 2026-06-11T06:13:04.523817Z UTC*
