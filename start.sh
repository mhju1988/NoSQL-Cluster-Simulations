#!/bin/bash
# Quick start script for NoSQL Cluster Simulation

set -e

echo "========================================"
echo "  NoSQL Cluster Simulation - Start"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Step 1: Starting Docker containers...${NC}"
docker-compose up -d

echo ""
echo -e "${YELLOW}Step 2: Waiting for services to initialize (30s)...${NC}"
sleep 30

echo ""
echo -e "${YELLOW}Step 3: Initializing MongoDB replica set...${NC}"
docker exec mongo1 bash /scripts/init-replica-set.sh

echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "========================================"
echo "  Access Points"
echo "========================================"
echo "MongoDB Primary:   localhost:27017"
echo "MongoDB Secondary: localhost:27018"
echo "MongoDB Secondary: localhost:27019"
echo "Prometheus:        http://localhost:9090"
echo "Grafana:           http://localhost:3000 (admin/admin)"
echo ""
echo "========================================"
echo "  Quick Commands"
echo "========================================"
echo "Run baseline test:"
echo "  docker exec test-orchestrator python load_generator.py --duration 60"
echo ""
echo "Run chaos scenarios:"
echo "  ./chaos/chaos-scenarios.sh"
echo ""
echo "Run automated tests:"
echo "  docker exec test-orchestrator python test_framework.py"
echo ""
echo "Check cluster status:"
echo "  docker exec mongo1 mongosh --eval 'rs.status()'"
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo "========================================"
