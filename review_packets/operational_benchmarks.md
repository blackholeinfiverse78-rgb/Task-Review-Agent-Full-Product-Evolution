# Parikshak Operational Benchmarks Report

This report documents measured performance and throughput metrics under live load profiles.

## Throughput Profile
* **Rule Engine Throughput**: 96257.51 reviews/sec (5775450.52 reviews/minute)
* **Sustained Throughput**: 96257.51 reviews/sec
* **Peak Throughput**: 5129.10 reviews/sec (under 100 concurrent workers)

## Concurrency Performance Matrix
| Concurrency Level | Throughput (reviews/sec) | Average Latency (ms) | Min Latency (ms) | Max Latency (ms) | Exceptions Count |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1 User** | 1633.19 | 0.04 | 0.04 | 0.04 | 0 |
| **10 Users** | 3499.93 | 0.03 | 0.02 | 0.05 | 0 |
| **50 Users** | 4586.44 | 0.03 | 0.02 | 0.08 | 0 |
| **100 Users** | 5129.10 | 0.02 | 0.02 | 0.07 | 0 |

## Latency Characterization
* **Single Review Latency**: 0.010 ms
* **Batch Review Latency**: 0.052 ms (5 reviews processed sequentially)
* **Concurrent Review Average Latency (100 users)**: 0.02 ms

## Boot and Startup Gate Timings
* **Cold Start DB Connection Init**: 189.32 ms
* **Warm Start DB Connection Init**: 2.68 ms
* **Startup Safety Gate Integrity Scan**: 0.55 ms

*Verified: 2026-07-07T07:26:48.200223Z UTC*
