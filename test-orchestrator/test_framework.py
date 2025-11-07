#!/usr/bin/env python3
"""
Automated Testing Framework for MongoDB Cluster
Orchestrates chaos scenarios with load testing and metrics collection
"""

import time
import json
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
import docker
from colorama import init, Fore, Style

from load_generator import LoadGenerator

init(autoreset=True)


class ChaosScenario:
    """Represents a chaos engineering scenario"""

    def __init__(self, name: str, description: str, duration: int, inject_fn, recover_fn=None):
        self.name = name
        self.description = description
        self.duration = duration
        self.inject_fn = inject_fn
        self.recover_fn = recover_fn


class TestFramework:
    """Automated testing framework for chaos scenarios"""

    def __init__(self, mongodb_uri: str, results_dir: str = "/results"):
        self.mongodb_uri = mongodb_uri
        self.results_dir = results_dir
        self.docker_client = docker.from_env()

        # Ensure results directory exists
        os.makedirs(results_dir, exist_ok=True)

        # Load generator
        self.load_generator = None

    def _log(self, message: str, level: str = "INFO"):
        """Colored logging"""
        colors = {
            "INFO": Fore.CYAN,
            "SUCCESS": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
        }
        color = colors.get(level, Fore.WHITE)
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] {level}: {message}")

    def setup_load_generator(
        self, threads: int = 10, write_ratio: float = 0.5, ops_per_sec: int = 100
    ):
        """Initialize the load generator"""
        self._log("Setting up load generator...")

        self.load_generator = LoadGenerator(
            connection_string=self.mongodb_uri,
            num_threads=threads,
            write_ratio=write_ratio,
            operations_per_second=ops_per_sec,
        )

        self.load_generator.connect()
        self._log("Load generator ready", "SUCCESS")

    def start_baseline(self, duration: int = 60):
        """Run baseline test without any chaos"""
        self._log("Starting baseline test...", "INFO")
        self._log(f"Duration: {duration}s", "INFO")

        self.load_generator.reset_stats()
        self.load_generator.start()

        time.sleep(duration)

        self.load_generator.stop()
        stats = self.load_generator.get_stats_dict()

        # Save baseline results
        baseline_file = os.path.join(self.results_dir, "baseline.json")
        with open(baseline_file, "w") as f:
            json.dump(stats, f, indent=2)

        self._log(f"Baseline test complete. Results: {baseline_file}", "SUCCESS")
        return stats

    def run_chaos_scenario(
        self, scenario: ChaosScenario, pre_chaos_duration: int = 30, post_chaos_duration: int = 30
    ) -> Dict:
        """
        Run a chaos scenario with load testing

        Args:
            scenario: ChaosScenario to execute
            pre_chaos_duration: Duration before injecting chaos
            post_chaos_duration: Duration after chaos ends

        Returns:
            Dictionary with test results
        """
        self._log(f"=" * 80, "INFO")
        self._log(f"CHAOS SCENARIO: {scenario.name}", "INFO")
        self._log(f"Description: {scenario.description}", "INFO")
        self._log(f"=" * 80, "INFO")

        results = {
            "scenario": scenario.name,
            "description": scenario.description,
            "start_time": datetime.utcnow().isoformat(),
            "phases": {},
        }

        # Reset and start load generator
        self.load_generator.reset_stats()
        self.load_generator.start()

        # Phase 1: Pre-chaos (baseline)
        self._log(f"Phase 1: Pre-chaos baseline ({pre_chaos_duration}s)", "INFO")
        time.sleep(pre_chaos_duration)
        results["phases"]["pre_chaos"] = self.load_generator.get_stats_dict()
        self.load_generator.print_stats()

        # Phase 2: Inject chaos
        self._log(f"Phase 2: Injecting chaos ({scenario.duration}s)", "WARNING")
        self.load_generator.reset_stats()

        try:
            scenario.inject_fn()
        except Exception as e:
            self._log(f"Error injecting chaos: {e}", "ERROR")
            results["error"] = str(e)

        time.sleep(scenario.duration)
        results["phases"]["during_chaos"] = self.load_generator.get_stats_dict()
        self.load_generator.print_stats()

        # Phase 3: Recovery
        if scenario.recover_fn:
            self._log("Phase 3: Initiating recovery", "INFO")
            try:
                scenario.recover_fn()
            except Exception as e:
                self._log(f"Error during recovery: {e}", "ERROR")

        self._log(f"Phase 3: Post-chaos recovery ({post_chaos_duration}s)", "INFO")
        self.load_generator.reset_stats()
        time.sleep(post_chaos_duration)
        results["phases"]["post_chaos"] = self.load_generator.get_stats_dict()
        self.load_generator.print_stats()

        # Stop load generator
        self.load_generator.stop()

        # Calculate impact metrics
        results["impact"] = self._calculate_impact(results["phases"])
        results["end_time"] = datetime.utcnow().isoformat()

        # Save results
        scenario_file = os.path.join(
            self.results_dir, f"scenario_{scenario.name.replace(' ', '_').lower()}.json"
        )
        with open(scenario_file, "w") as f:
            json.dump(results, f, indent=2)

        self._log(f"Scenario complete. Results: {scenario_file}", "SUCCESS")
        self._print_impact_summary(results["impact"])

        return results

    def _calculate_impact(self, phases: Dict) -> Dict:
        """Calculate impact metrics by comparing phases"""
        pre = phases.get("pre_chaos", {})
        during = phases.get("during_chaos", {})
        post = phases.get("post_chaos", {})

        def safe_divide(a, b):
            return (a / b) if b != 0 else 0

        def get_success_rate(phase):
            ops = phase.get("operations", {})
            total_reads = ops.get("reads_success", 0) + ops.get("reads_failed", 0)
            total_writes = ops.get("writes_success", 0) + ops.get("writes_failed", 0)

            read_rate = safe_divide(ops.get("reads_success", 0), total_reads) * 100
            write_rate = safe_divide(ops.get("writes_success", 0), total_writes) * 100

            return {"read": read_rate, "write": write_rate}

        pre_rates = get_success_rate(pre)
        during_rates = get_success_rate(during)
        post_rates = get_success_rate(post)

        impact = {
            "availability_impact": {
                "read_success_rate": {
                    "pre_chaos": pre_rates["read"],
                    "during_chaos": during_rates["read"],
                    "post_chaos": post_rates["read"],
                    "degradation_pct": pre_rates["read"] - during_rates["read"],
                },
                "write_success_rate": {
                    "pre_chaos": pre_rates["write"],
                    "during_chaos": during_rates["write"],
                    "post_chaos": post_rates["write"],
                    "degradation_pct": pre_rates["write"] - during_rates["write"],
                },
            },
            "latency_impact": {
                "read_p99": {
                    "pre_chaos": pre.get("latency", {}).get("read", {}).get("p99", 0),
                    "during_chaos": during.get("latency", {}).get("read", {}).get("p99", 0),
                    "post_chaos": post.get("latency", {}).get("read", {}).get("p99", 0),
                },
                "write_p99": {
                    "pre_chaos": pre.get("latency", {}).get("write", {}).get("p99", 0),
                    "during_chaos": during.get("latency", {}).get("write", {}).get("p99", 0),
                    "post_chaos": post.get("latency", {}).get("write", {}).get("p99", 0),
                },
            },
        }

        return impact

    def _print_impact_summary(self, impact: Dict):
        """Print impact summary"""
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}IMPACT SUMMARY")
        print(f"{Fore.CYAN}{'=' * 80}")

        avail = impact["availability_impact"]
        latency = impact["latency_impact"]

        print(f"\n{Fore.WHITE}Availability Impact:")
        print(
            f"  Read Success Rate:  "
            f"{avail['read_success_rate']['pre_chaos']:.1f}% → "
            f"{avail['read_success_rate']['during_chaos']:.1f}% → "
            f"{avail['read_success_rate']['post_chaos']:.1f}%"
        )
        print(
            f"  Write Success Rate: "
            f"{avail['write_success_rate']['pre_chaos']:.1f}% → "
            f"{avail['write_success_rate']['during_chaos']:.1f}% → "
            f"{avail['write_success_rate']['post_chaos']:.1f}%"
        )

        print(f"\n{Fore.WHITE}Latency Impact (P99):")
        print(
            f"  Read Latency:  "
            f"{latency['read_p99']['pre_chaos']:.2f}ms → "
            f"{latency['read_p99']['during_chaos']:.2f}ms → "
            f"{latency['read_p99']['post_chaos']:.2f}ms"
        )
        print(
            f"  Write Latency: "
            f"{latency['write_p99']['pre_chaos']:.2f}ms → "
            f"{latency['write_p99']['during_chaos']:.2f}ms → "
            f"{latency['write_p99']['post_chaos']:.2f}ms"
        )

        print(f"{Fore.CYAN}{'=' * 80}\n")

    # Chaos injection methods
    def _stop_container(self, container_name: str):
        """Stop a Docker container"""
        try:
            container = self.docker_client.containers.get(container_name)
            container.stop()
            self._log(f"Stopped container: {container_name}", "WARNING")
        except Exception as e:
            self._log(f"Error stopping container {container_name}: {e}", "ERROR")

    def _start_container(self, container_name: str):
        """Start a Docker container"""
        try:
            container = self.docker_client.containers.get(container_name)
            container.start()
            self._log(f"Started container: {container_name}", "SUCCESS")
        except Exception as e:
            self._log(f"Error starting container {container_name}: {e}", "ERROR")

    def _restart_container(self, container_name: str):
        """Restart a Docker container"""
        try:
            container = self.docker_client.containers.get(container_name)
            container.restart()
            self._log(f"Restarted container: {container_name}", "WARNING")
        except Exception as e:
            self._log(f"Error restarting container {container_name}: {e}", "ERROR")

    # Pre-defined chaos scenarios
    def get_predefined_scenarios(self) -> List[ChaosScenario]:
        """Get list of predefined chaos scenarios"""
        return [
            ChaosScenario(
                name="Node Failure",
                description="Simulate primary node failure and failover",
                duration=30,
                inject_fn=lambda: self._stop_container("mongo1"),
                recover_fn=lambda: self._start_container("mongo1"),
            ),
            ChaosScenario(
                name="Secondary Failure",
                description="Simulate secondary node failure",
                duration=30,
                inject_fn=lambda: self._stop_container("mongo2"),
                recover_fn=lambda: self._start_container("mongo2"),
            ),
            ChaosScenario(
                name="Split Brain",
                description="Network partition creating split-brain scenario",
                duration=60,
                inject_fn=lambda: subprocess.run(
                    ["docker", "exec", "pumba", "pumba", "netem", "--duration", "60s",
                     "--interface", "eth0", "loss", "--percent", "100", "mongo1"],
                    capture_output=True,
                ),
            ),
            ChaosScenario(
                name="Rolling Restart",
                description="Rolling restart of all nodes",
                duration=90,
                inject_fn=lambda: [
                    self._restart_container("mongo1"),
                    time.sleep(30),
                    self._restart_container("mongo2"),
                    time.sleep(30),
                    self._restart_container("mongo3"),
                ],
            ),
        ]

    def run_all_scenarios(self):
        """Run all predefined scenarios"""
        self._log("Running all chaos scenarios...", "INFO")

        scenarios = self.get_predefined_scenarios()
        all_results = []

        for scenario in scenarios:
            result = self.run_chaos_scenario(scenario)
            all_results.append(result)

            # Wait between scenarios
            self._log("Waiting 30s before next scenario...", "INFO")
            time.sleep(30)

        # Generate summary report
        summary_file = os.path.join(self.results_dir, "summary.json")
        with open(summary_file, "w") as f:
            json.dump(
                {
                    "test_run": datetime.utcnow().isoformat(),
                    "scenarios": all_results,
                },
                f,
                indent=2,
            )

        self._log(f"All scenarios complete. Summary: {summary_file}", "SUCCESS")


def main():
    """Main entry point"""
    mongodb_uri = os.getenv(
        "MONGODB_URI",
        "mongodb://admin:password123@mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0",
    )

    framework = TestFramework(mongodb_uri)
    framework.setup_load_generator(threads=10, write_ratio=0.5, ops_per_sec=100)

    # Run baseline
    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}STARTING AUTOMATED CHAOS TESTING")
    print(f"{Fore.CYAN}{'=' * 80}\n")

    framework.start_baseline(duration=60)

    # Run all chaos scenarios
    framework.run_all_scenarios()

    print(f"\n{Fore.GREEN}{'=' * 80}")
    print(f"{Fore.GREEN}ALL TESTS COMPLETE")
    print(f"{Fore.GREEN}{'=' * 80}")


if __name__ == "__main__":
    main()
