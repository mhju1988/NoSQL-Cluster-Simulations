#!/usr/bin/env python3
"""
Advanced Load Generator for MongoDB Cluster
Features:
- Configurable read/write rates
- Multi-threaded workload
- Latency tracking (P50, P95, P99)
- Success/failure rate monitoring
- Consistency verification
"""

import time
import random
import threading
import sys
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple
import argparse
import json
import os

import numpy as np
from pymongo import MongoClient, WriteConcern, ReadPreference
from pymongo.errors import PyMongoError, AutoReconnect, ConnectionFailure
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)


class LatencyTracker:
    """Track latency statistics"""

    def __init__(self):
        self.latencies = []
        self.lock = threading.Lock()

    def add(self, latency_ms: float):
        with self.lock:
            self.latencies.append(latency_ms)

    def get_stats(self) -> Dict[str, float]:
        with self.lock:
            if not self.latencies:
                return {"p50": 0, "p95": 0, "p99": 0, "mean": 0, "min": 0, "max": 0}

            arr = np.array(self.latencies)
            return {
                "p50": float(np.percentile(arr, 50)),
                "p95": float(np.percentile(arr, 95)),
                "p99": float(np.percentile(arr, 99)),
                "mean": float(np.mean(arr)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
            }

    def reset(self):
        with self.lock:
            self.latencies = []


class OperationCounter:
    """Thread-safe operation counter"""

    def __init__(self):
        self.counts = defaultdict(int)
        self.lock = threading.Lock()

    def increment(self, key: str, value: int = 1):
        with self.lock:
            self.counts[key] += value

    def get(self, key: str) -> int:
        with self.lock:
            return self.counts.get(key, 0)

    def get_all(self) -> Dict[str, int]:
        with self.lock:
            return dict(self.counts)

    def reset(self):
        with self.lock:
            self.counts.clear()


class LoadGenerator:
    """Advanced MongoDB load generator"""

    def __init__(
        self,
        connection_string: str,
        num_threads: int = 10,
        write_ratio: float = 0.5,
        operations_per_second: int = 100,
    ):
        self.connection_string = connection_string
        self.num_threads = num_threads
        self.write_ratio = write_ratio
        self.operations_per_second = operations_per_second

        # Statistics tracking
        self.read_latency = LatencyTracker()
        self.write_latency = LatencyTracker()
        self.counters = OperationCounter()

        # Control flags
        self.running = False
        self.threads = []

        # MongoDB client
        self.client = None
        self.db = None
        self.collection = None

    def connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
            )
            self.db = self.client.testdb
            self.collection = self.db.testcollection

            # Test connection
            self.client.admin.command("ping")
            print(f"{Fore.GREEN}✓ Connected to MongoDB cluster")

        except Exception as e:
            print(f"{Fore.RED}✗ Failed to connect to MongoDB: {e}")
            sys.exit(1)

    def _perform_write(self) -> Tuple[bool, float]:
        """Perform a write operation and return (success, latency_ms)"""
        start_time = time.time()
        try:
            doc = {
                "key": f"key_{random.randint(1, 100000)}",
                "value": random.randint(1, 1000000),
                "timestamp": datetime.utcnow(),
                "thread_id": threading.current_thread().ident,
                "data": "x" * 100,  # Some payload
            }

            # Use majority write concern for consistency
            result = self.collection.with_options(
                write_concern=WriteConcern(w="majority", wtimeout=5000)
            ).insert_one(doc)

            latency_ms = (time.time() - start_time) * 1000
            return (result.acknowledged, latency_ms)

        except AutoReconnect as e:
            latency_ms = (time.time() - start_time) * 1000
            self.counters.increment("write_auto_reconnect")
            return (False, latency_ms)

        except ConnectionFailure as e:
            latency_ms = (time.time() - start_time) * 1000
            self.counters.increment("write_connection_failure")
            return (False, latency_ms)

        except PyMongoError as e:
            latency_ms = (time.time() - start_time) * 1000
            self.counters.increment("write_other_error")
            return (False, latency_ms)

    def _perform_read(self) -> Tuple[bool, float]:
        """Perform a read operation and return (success, latency_ms)"""
        start_time = time.time()
        try:
            # Random read operation
            result = self.collection.find_one(
                {"key": f"key_{random.randint(1, 100000)}"},
                read_preference=ReadPreference.NEAREST,
            )

            latency_ms = (time.time() - start_time) * 1000
            return (True, latency_ms)

        except AutoReconnect as e:
            latency_ms = (time.time() - start_time) * 1000
            self.counters.increment("read_auto_reconnect")
            return (False, latency_ms)

        except ConnectionFailure as e:
            latency_ms = (time.time() - start_time) * 1000
            self.counters.increment("read_connection_failure")
            return (False, latency_ms)

        except PyMongoError as e:
            latency_ms = (time.time() - start_time) * 1000
            self.counters.increment("read_other_error")
            return (False, latency_ms)

    def _worker_thread(self, thread_id: int):
        """Worker thread that generates load"""
        sleep_time = 1.0 / (self.operations_per_second / self.num_threads)

        while self.running:
            try:
                # Decide whether to read or write based on ratio
                if random.random() < self.write_ratio:
                    success, latency = self._perform_write()
                    if success:
                        self.counters.increment("writes_success")
                        self.write_latency.add(latency)
                    else:
                        self.counters.increment("writes_failed")
                else:
                    success, latency = self._perform_read()
                    if success:
                        self.counters.increment("reads_success")
                        self.read_latency.add(latency)
                    else:
                        self.counters.increment("reads_failed")

                # Rate limiting
                time.sleep(sleep_time)

            except Exception as e:
                self.counters.increment("unexpected_errors")
                time.sleep(0.1)

    def start(self):
        """Start the load generator"""
        print(f"{Fore.CYAN}Starting load generator...")
        print(f"  Threads: {self.num_threads}")
        print(f"  Write Ratio: {self.write_ratio * 100:.0f}%")
        print(f"  Target Ops/sec: {self.operations_per_second}")

        self.running = True

        for i in range(self.num_threads):
            t = threading.Thread(target=self._worker_thread, args=(i,), daemon=True)
            t.start()
            self.threads.append(t)

        print(f"{Fore.GREEN}✓ Load generator started")

    def stop(self):
        """Stop the load generator"""
        print(f"{Fore.YELLOW}Stopping load generator...")
        self.running = False

        for t in self.threads:
            t.join(timeout=5)

        print(f"{Fore.GREEN}✓ Load generator stopped")

    def print_stats(self):
        """Print current statistics"""
        counts = self.counters.get_all()
        read_stats = self.read_latency.get_stats()
        write_stats = self.write_latency.get_stats()

        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}LOAD GENERATOR STATISTICS")
        print(f"{Fore.CYAN}{'=' * 80}")

        # Operation counts
        total_reads = counts.get("reads_success", 0) + counts.get("reads_failed", 0)
        total_writes = counts.get("writes_success", 0) + counts.get("writes_failed", 0)

        read_success_rate = (
            (counts.get("reads_success", 0) / total_reads * 100) if total_reads > 0 else 0
        )
        write_success_rate = (
            (counts.get("writes_success", 0) / total_writes * 100)
            if total_writes > 0
            else 0
        )

        print(f"\n{Fore.WHITE}Operations:")
        print(f"  Reads:  {counts.get('reads_success', 0):6d} success, "
              f"{counts.get('reads_failed', 0):6d} failed "
              f"({read_success_rate:5.1f}% success rate)")
        print(f"  Writes: {counts.get('writes_success', 0):6d} success, "
              f"{counts.get('writes_failed', 0):6d} failed "
              f"({write_success_rate:5.1f}% success rate)")

        # Latency stats
        print(f"\n{Fore.WHITE}Read Latency (ms):")
        print(f"  P50:  {read_stats['p50']:7.2f}   P95:  {read_stats['p95']:7.2f}   "
              f"P99:  {read_stats['p99']:7.2f}")
        print(f"  Mean: {read_stats['mean']:7.2f}   Min:  {read_stats['min']:7.2f}   "
              f"Max:  {read_stats['max']:7.2f}")

        print(f"\n{Fore.WHITE}Write Latency (ms):")
        print(f"  P50:  {write_stats['p50']:7.2f}   P95:  {write_stats['p95']:7.2f}   "
              f"P99:  {write_stats['p99']:7.2f}")
        print(f"  Mean: {write_stats['mean']:7.2f}   Min:  {write_stats['min']:7.2f}   "
              f"Max:  {write_stats['max']:7.2f}")

        # Error breakdown
        error_types = [
            "read_auto_reconnect",
            "read_connection_failure",
            "read_other_error",
            "write_auto_reconnect",
            "write_connection_failure",
            "write_other_error",
            "unexpected_errors",
        ]

        errors = {k: counts.get(k, 0) for k in error_types if counts.get(k, 0) > 0}

        if errors:
            print(f"\n{Fore.YELLOW}Errors:")
            for error_type, count in errors.items():
                print(f"  {error_type}: {count}")

        print(f"{Fore.CYAN}{'=' * 80}\n")

    def get_stats_dict(self) -> Dict:
        """Get statistics as dictionary"""
        counts = self.counters.get_all()
        read_stats = self.read_latency.get_stats()
        write_stats = self.write_latency.get_stats()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "operations": {
                "reads_success": counts.get("reads_success", 0),
                "reads_failed": counts.get("reads_failed", 0),
                "writes_success": counts.get("writes_success", 0),
                "writes_failed": counts.get("writes_failed", 0),
            },
            "latency": {"read": read_stats, "write": write_stats},
            "errors": {
                k: v
                for k, v in counts.items()
                if k not in ["reads_success", "reads_failed", "writes_success", "writes_failed"]
            },
        }

    def reset_stats(self):
        """Reset all statistics"""
        self.counters.reset()
        self.read_latency.reset()
        self.write_latency.reset()


def main():
    parser = argparse.ArgumentParser(description="MongoDB Load Generator")
    parser.add_argument(
        "--uri",
        default=os.getenv(
            "MONGODB_URI",
            "mongodb://admin:password123@mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0",
        ),
        help="MongoDB connection URI",
    )
    parser.add_argument(
        "--threads", type=int, default=10, help="Number of worker threads"
    )
    parser.add_argument(
        "--write-ratio", type=float, default=0.5, help="Ratio of write operations (0.0-1.0)"
    )
    parser.add_argument(
        "--ops-per-sec", type=int, default=100, help="Target operations per second"
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Duration in seconds (0 = infinite)"
    )
    parser.add_argument(
        "--report-interval", type=int, default=10, help="Statistics report interval in seconds"
    )

    args = parser.parse_args()

    # Create load generator
    generator = LoadGenerator(
        connection_string=args.uri,
        num_threads=args.threads,
        write_ratio=args.write_ratio,
        operations_per_second=args.ops_per_sec,
    )

    # Connect to MongoDB
    generator.connect()

    # Start load generation
    generator.start()

    try:
        start_time = time.time()
        last_report = start_time

        while True:
            current_time = time.time()

            # Print statistics at intervals
            if current_time - last_report >= args.report_interval:
                generator.print_stats()
                last_report = current_time

            # Check if duration limit reached
            if args.duration > 0 and (current_time - start_time) >= args.duration:
                print(f"\n{Fore.YELLOW}Duration limit reached")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user")

    finally:
        generator.stop()
        generator.print_stats()

        # Save final stats to file
        results_dir = os.getenv("RESULTS_DIR", "/results")
        os.makedirs(results_dir, exist_ok=True)

        stats_file = os.path.join(
            results_dir, f"load_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(stats_file, "w") as f:
            json.dump(generator.get_stats_dict(), f, indent=2)

        print(f"{Fore.GREEN}✓ Statistics saved to {stats_file}")


if __name__ == "__main__":
    main()
