# Parikshak Operational Benchmarks Report

This report documents measured performance and throughput metrics under live load profiles.

## Throughput Profile
* **Rule Engine Throughput**: 138881.17 reviews/sec (8332870.40 reviews/minute)
* **Sustained Throughput**: 138881.17 reviews/sec
* **Peak Throughput**: 6378.20 reviews/sec (under 100 concurrent workers)

## Concurrency Performance Matrix
| Concurrency Level | Throughput (reviews/sec) | Average Latency (ms) | Min Latency (ms) | Max Latency (ms) | Exceptions Count |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1 User** | 1917.55 | 0.03 | 0.03 | 0.03 | 0 |
| **10 Users** | 4086.14 | 0.02 | 0.02 | 0.04 | 0 |
| **50 Users** | 6165.38 | 0.02 | 0.01 | 0.03 | 0 |
| **100 Users** | 6378.20 | 0.02 | 0.01 | 0.03 | 0 |

## Latency Characterization
* **Single Review Latency**: 0.007 ms
* **Batch Review Latency**: 0.036 ms (5 reviews processed sequentially)
* **Concurrent Review Average Latency (100 users)**: 0.02 ms

## Boot and Startup Gate Timings
* **Cold Start DB Connection Init**: 239.32 ms
* **Warm Start DB Connection Init**: 1.90 ms
* **Startup Safety Gate Integrity Scan**: 0.58 ms

*Verified: 2026-07-03T08:06:50.442039Z UTC*
