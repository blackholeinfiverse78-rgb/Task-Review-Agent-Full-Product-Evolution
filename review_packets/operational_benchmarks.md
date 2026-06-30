# Parikshak Operational Benchmarks Report

This report documents measured performance and throughput metrics under live load profiles.

## Throughput Profile
* **Rule Engine Throughput**: 73399.88 reviews/sec (4403992.95 reviews/minute)
* **Sustained Throughput**: 73399.88 reviews/sec
* **Peak Throughput**: 2399.94 reviews/sec (under 100 concurrent workers)

## Concurrency Performance Matrix
| Concurrency Level | Throughput (reviews/sec) | Average Latency (ms) | Min Latency (ms) | Max Latency (ms) | Exceptions Count |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1 User** | 825.76 | 0.09 | 0.09 | 0.09 | 0 |
| **10 Users** | 2691.21 | 0.04 | 0.03 | 0.06 | 0 |
| **50 Users** | 2844.92 | 0.04 | 0.02 | 0.08 | 0 |
| **100 Users** | 2399.94 | 0.05 | 0.02 | 0.25 | 0 |

## Latency Characterization
* **Single Review Latency**: 0.014 ms
* **Batch Review Latency**: 0.068 ms (5 reviews processed sequentially)
* **Concurrent Review Average Latency (100 users)**: 0.05 ms

## Boot and Startup Gate Timings
* **Cold Start DB Connection Init**: 274.99 ms
* **Warm Start DB Connection Init**: 2.61 ms
* **Startup Safety Gate Integrity Scan**: 1.27 ms

*Verified: 2026-06-30T10:38:25.380578Z UTC*
