#!/bin/bash
# Stop script for NoSQL Cluster Simulation

set -e

echo "========================================"
echo "  NoSQL Cluster Simulation - Stop"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Stopping all containers...${NC}"
docker-compose down

echo ""
echo -e "${GREEN}✓ All containers stopped${NC}"
echo ""

read -p "Do you want to remove all data volumes? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}Removing data volumes...${NC}"
    docker-compose down -v
    echo -e "${GREEN}✓ All volumes removed${NC}"
else
    echo -e "${YELLOW}Data volumes preserved${NC}"
fi

echo ""
echo "========================================"
echo "  Cleanup Complete"
echo "========================================"
