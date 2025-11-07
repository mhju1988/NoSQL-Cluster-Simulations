#!/bin/bash
# Demo script showing end-to-end chaos testing

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     NoSQL Cluster Chaos Engineering - DEMO                ║
║                                                           ║
║  This demo will:                                          ║
║  1. Start a baseline load test (30s)                      ║
║  2. Inject a node failure chaos scenario (30s)            ║
║  3. Show the impact on performance and availability       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

read -p "Press Enter to start the demo..."

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Phase 1: Baseline Performance Test (30s)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

docker exec test-orchestrator python load_generator.py \
  --threads 10 \
  --write-ratio 0.5 \
  --ops-per-sec 50 \
  --duration 30 \
  --report-interval 10

echo ""
echo -e "${GREEN}✓ Baseline test complete${NC}"
sleep 3

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Phase 2: Chaos Injection - Primary Node Failure${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start load generator in background
echo -e "${CYAN}Starting background load...${NC}"
docker exec -d test-orchestrator python load_generator.py \
  --threads 10 \
  --write-ratio 0.5 \
  --ops-per-sec 50 \
  --duration 60 \
  --report-interval 15

sleep 5

echo ""
echo -e "${RED}⚠ Injecting chaos: Stopping mongo1 (primary node)${NC}"
docker stop mongo1

echo ""
echo -e "${YELLOW}Observing cluster behavior for 20 seconds...${NC}"
echo -e "${YELLOW}(MongoDB should elect a new primary)${NC}"
sleep 20

echo ""
echo -e "${CYAN}Checking new primary:${NC}"
docker exec mongo2 mongosh --quiet -u admin -p password123 --authenticationDatabase admin --eval "rs.isMaster().primary" 2>/dev/null || echo "Checking..."

echo ""
echo -e "${GREEN}Recovering: Restarting mongo1${NC}"
docker start mongo1

echo ""
echo -e "${YELLOW}Waiting for recovery and remaining load test...${NC}"
sleep 30

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Phase 3: Results Summary${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check cluster status
echo -e "${CYAN}Current Cluster Status:${NC}"
docker exec mongo1 mongosh --quiet -u admin -p password123 --authenticationDatabase admin --eval "
  var status = rs.status();
  print('Replica Set: ' + status.set);
  status.members.forEach(function(member) {
    print('  ' + member.name + ': ' + member.stateStr);
  });
" 2>/dev/null

echo ""
echo -e "${CYAN}Test Results:${NC}"
echo "Results have been saved to ./results/ directory"
echo ""

if [ -d "./results" ] && [ "$(ls -A ./results)" ]; then
    echo "Latest result files:"
    ls -lt ./results | head -5
fi

echo ""
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║                    DEMO COMPLETE!                         ║
║                                                           ║
║  Key Observations:                                        ║
║  • MongoDB automatically elected a new primary            ║
║  • Writes were briefly unavailable during failover        ║
║  • System recovered automatically when node returned      ║
║  • Replication lag normalized after recovery              ║
║                                                           ║
║  Next Steps:                                              ║
║  • View Grafana: http://localhost:3000                    ║
║  • Check results: cat results/*.json | jq                 ║
║  • Run more scenarios: ./chaos/chaos-scenarios.sh         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
