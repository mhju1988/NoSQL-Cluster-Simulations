#!/bin/bash
# Status check script for NoSQL Cluster Simulation

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================"
echo "  NoSQL Cluster Status"
echo "========================================${NC}"
echo ""

# Check Docker containers
echo -e "${YELLOW}Docker Containers:${NC}"
docker-compose ps

echo ""
echo -e "${YELLOW}MongoDB Replica Set Status:${NC}"
docker exec mongo1 mongosh --quiet -u admin -p password123 --authenticationDatabase admin --eval "rs.status()" 2>/dev/null || echo -e "${RED}Failed to get replica set status${NC}"

echo ""
echo -e "${YELLOW}MongoDB Primary Node:${NC}"
docker exec mongo1 mongosh --quiet -u admin -p password123 --authenticationDatabase admin --eval "rs.isMaster().primary" 2>/dev/null || echo -e "${RED}Failed to determine primary${NC}"

echo ""
echo -e "${YELLOW}Collection Stats:${NC}"
docker exec mongo1 mongosh --quiet -u admin -p password123 --authenticationDatabase admin --eval "use testdb; db.testcollection.countDocuments({})" 2>/dev/null || echo -e "${RED}Failed to get collection stats${NC}"

echo ""
echo -e "${YELLOW}Service URLs:${NC}"
echo "  Prometheus:  http://localhost:9090"
echo "  Grafana:     http://localhost:3000"

echo ""
echo -e "${CYAN}========================================${NC}"
