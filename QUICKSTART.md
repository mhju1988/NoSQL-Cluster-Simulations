# Quick Start Guide

Get up and running with NoSQL Cluster Simulations in 5 minutes.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum

## Installation (1 minute)

```bash
# Clone the repository
git clone https://github.com/yourusername/NoSQL-Cluster-Simulations.git
cd NoSQL-Cluster-Simulations

# Start everything
./start.sh
```

This will:
- Start 3 MongoDB nodes in a replica set
- Start Prometheus and Grafana monitoring
- Initialize the replica set
- Set up chaos engineering tools

## Verify Installation (30 seconds)

```bash
# Check cluster status
./status.sh

# Expected output: All 3 nodes should be running
```

## Run Your First Test (2 minutes)

### Option 1: Interactive Demo

```bash
./demo.sh
```

This runs an automated demo that:
1. Performs a baseline load test
2. Injects a node failure
3. Shows the cluster recovering automatically
4. Displays impact analysis

### Option 2: Manual Testing

```bash
# 1. Start load generator (runs in foreground)
docker exec test-orchestrator python load_generator.py \
  --duration 60 \
  --threads 10 \
  --write-ratio 0.5

# 2. In another terminal, inject chaos
./chaos/chaos-scenarios.sh node-failure mongo1

# 3. Observe the impact in the load generator output
```

## View Monitoring Dashboards (30 seconds)

```bash
# Open Grafana in your browser
open http://localhost:3000

# Login: admin / admin
# Navigate to: Dashboards → MongoDB Cluster Monitoring
```

You'll see:
- Node health status
- Operations per second
- Replication lag
- Latency metrics (P50, P95, P99)

## Understanding Results

Results are saved in `./results/` directory:

```bash
# View latest results
ls -lt results/

# Pretty-print JSON results (if jq is installed)
cat results/baseline.json | jq .

# Key metrics to look for:
# - operations.reads_success / writes_success
# - latency.read.p99 / latency.write.p99
# - impact.availability_impact
```

## Common Commands

### Cluster Management

```bash
# Start cluster
./start.sh

# Stop cluster (keep data)
docker-compose down

# Stop and remove all data
./stop.sh

# Check status
./status.sh

# View logs
docker-compose logs -f
```

### Load Testing

```bash
# Light load (50 ops/sec)
docker exec test-orchestrator python load_generator.py \
  --ops-per-sec 50 --duration 60

# Heavy load (500 ops/sec, 50 threads)
docker exec test-orchestrator python load_generator.py \
  --ops-per-sec 500 --threads 50 --duration 60

# Write-heavy workload (80% writes)
docker exec test-orchestrator python load_generator.py \
  --write-ratio 0.8 --duration 60

# Read-heavy workload (80% reads)
docker exec test-orchestrator python load_generator.py \
  --write-ratio 0.2 --duration 60
```

### Chaos Scenarios

```bash
# Interactive menu
./chaos/chaos-scenarios.sh

# Specific scenarios
./chaos/chaos-scenarios.sh node-failure mongo1
./chaos/chaos-scenarios.sh network-delay 200 30 mongo2
./chaos/chaos-scenarios.sh packet-loss 30 30 mongo3
./chaos/chaos-scenarios.sh cpu-stress 30 mongo1
./chaos/chaos-scenarios.sh rolling-restart

# Run all scenarios
./chaos/chaos-scenarios.sh all
```

### Automated Testing

```bash
# Run complete test suite
docker exec test-orchestrator python test_framework.py

# Results will be in ./results/
# - baseline.json
# - scenario_*.json
# - summary.json
```

### MongoDB Operations

```bash
# Connect to primary
docker exec -it mongo1 mongosh -u admin -p password123

# Check replica set status
docker exec mongo1 mongosh --quiet -u admin -p password123 --eval "rs.status()"

# Check primary node
docker exec mongo1 mongosh --quiet -u admin -p password123 --eval "rs.isMaster().primary"

# Count documents
docker exec mongo1 mongosh --quiet -u admin -p password123 --eval "use testdb; db.testcollection.countDocuments({})"
```

## Typical Workflow

1. **Start cluster**: `./start.sh`
2. **Run baseline**: Get baseline performance metrics
   ```bash
   docker exec test-orchestrator python load_generator.py --duration 60
   ```
3. **Inject chaos**: Choose a chaos scenario
   ```bash
   ./chaos/chaos-scenarios.sh
   ```
4. **Observe impact**: Watch metrics in Grafana and load generator output
5. **Analyze results**: Check `./results/*.json`
6. **Cleanup**: `./stop.sh`

## Troubleshooting

### Containers won't start
```bash
# Check Docker resources
docker system df

# Restart Docker daemon
sudo systemctl restart docker  # Linux
# or restart Docker Desktop      # Mac/Windows
```

### Replica set won't initialize
```bash
# Manually initialize
docker exec mongo1 mongosh -u admin -p password123 --eval "rs.initiate()"

# Wait 10 seconds, then add nodes
docker exec mongo1 mongosh -u admin -p password123 --eval "rs.add('mongo2:27017')"
docker exec mongo1 mongosh -u admin -p password123 --eval "rs.add('mongo3:27017')"
```

### Load generator fails to connect
```bash
# Check network
docker exec test-orchestrator ping mongo1

# Restart test orchestrator
docker-compose restart test-orchestrator
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore [CONTRIBUTING.md](CONTRIBUTING.md) to add your own scenarios
- Check out the [chaos scenarios](chaos/chaos-scenarios.sh) source code
- Experiment with different load patterns
- Create custom Grafana dashboards

## Quick Tips

💡 **Tip 1**: Run `./status.sh` frequently to check cluster health

💡 **Tip 2**: Use Grafana for real-time monitoring during chaos tests

💡 **Tip 3**: Compare `baseline.json` with `scenario_*.json` to quantify impact

💡 **Tip 4**: Start with light load (50 ops/sec) and increase gradually

💡 **Tip 5**: Allow 10-15 seconds between scenarios for cluster to stabilize

## Support

- **Documentation**: See [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/NoSQL-Cluster-Simulations/issues)
- **Examples**: Run `./demo.sh` for a guided walkthrough

---

**Ready to break things?** Start with `./demo.sh` to see chaos engineering in action! 🚀
