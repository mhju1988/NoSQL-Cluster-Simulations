#!/bin/bash
# Comprehensive Chaos Engineering Scenarios for MongoDB Cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for recovery
wait_for_recovery() {
    local seconds=$1
    log_info "Waiting ${seconds}s for recovery..."
    sleep "$seconds"
}

# Scenario 1: Node Failure - Kill a MongoDB node
scenario_node_failure() {
    local node=${1:-mongo1}
    log_warning "SCENARIO: Node Failure - Killing $node"

    docker stop "$node"
    log_info "$node stopped"

    wait_for_recovery 20

    docker start "$node"
    log_info "$node restarted"
}

# Scenario 2: Network Partition - Split Brain
scenario_network_partition() {
    log_warning "SCENARIO: Network Partition - Creating split-brain"

    # Isolate mongo1 from mongo2 and mongo3
    docker exec pumba pumba netem --duration 60s --interface eth0 loss --percent 100 mongo1 &

    log_info "Network partition created - mongo1 isolated for 60s"
    wait_for_recovery 65

    log_info "Network partition healed"
}

# Scenario 3: Network Delay (Latency)
scenario_network_delay() {
    local delay_ms=${1:-200}
    local duration=${2:-30}
    local node=${3:-mongo2}

    log_warning "SCENARIO: Network Delay - Adding ${delay_ms}ms latency to $node for ${duration}s"

    docker exec pumba pumba netem --duration "${duration}s" --interface eth0 delay --time "$delay_ms" "$node" &

    wait_for_recovery "$((duration + 5))"

    log_info "Network delay removed"
}

# Scenario 4: Packet Loss
scenario_packet_loss() {
    local loss_percent=${1:-30}
    local duration=${2:-30}
    local node=${3:-mongo3}

    log_warning "SCENARIO: Packet Loss - ${loss_percent}% packet loss on $node for ${duration}s"

    docker exec pumba pumba netem --duration "${duration}s" --interface eth0 loss --percent "$loss_percent" "$node" &

    wait_for_recovery "$((duration + 5))"

    log_info "Packet loss scenario ended"
}

# Scenario 5: CPU Stress
scenario_cpu_stress() {
    local duration=${1:-30}
    local node=${2:-mongo1}

    log_warning "SCENARIO: CPU Stress - Stressing $node for ${duration}s"

    docker exec "$node" bash -c "timeout ${duration}s sh -c 'yes > /dev/null' &" || true

    wait_for_recovery "$((duration + 5))"

    log_info "CPU stress ended"
}

# Scenario 6: Memory Stress
scenario_memory_stress() {
    local duration=${1:-30}
    local node=${2:-mongo2}

    log_warning "SCENARIO: Memory Stress - Filling memory on $node for ${duration}s"

    docker exec "$node" bash -c "timeout ${duration}s sh -c '
        tmpfile=\$(mktemp)
        for i in {1..50}; do
            dd if=/dev/zero of=\$tmpfile bs=1M count=10 2>/dev/null
        done
        rm -f \$tmpfile
    ' &" || true

    wait_for_recovery "$((duration + 5))"

    log_info "Memory stress ended"
}

# Scenario 7: Disk I/O Stress
scenario_disk_stress() {
    local duration=${1:-30}
    local node=${2:-mongo3}

    log_warning "SCENARIO: Disk I/O Stress - Saturating disk I/O on $node for ${duration}s"

    docker exec "$node" bash -c "timeout ${duration}s sh -c '
        for i in {1..5}; do
            dd if=/dev/zero of=/tmp/test_\$i bs=1M count=100 oflag=direct 2>/dev/null &
        done
        wait
        rm -f /tmp/test_*
    ' &" || true

    wait_for_recovery "$((duration + 5))"

    log_info "Disk I/O stress ended"
}

# Scenario 8: Clock Skew
scenario_clock_skew() {
    local skew_seconds=${1:-300}
    local node=${2:-mongo2}

    log_warning "SCENARIO: Clock Skew - Setting $node clock ahead by ${skew_seconds}s"

    # Save current time
    docker exec "$node" date > /tmp/original_time_"$node"

    # Set clock ahead
    docker exec "$node" date -s "+${skew_seconds} seconds" || log_error "Failed to set clock"

    wait_for_recovery 30

    # Restore clock (sync with host)
    docker exec "$node" hwclock --hctosys 2>/dev/null || true

    log_info "Clock skew scenario ended"
}

# Scenario 9: Byzantine Failure (Simulated data corruption)
scenario_byzantine_failure() {
    local node=${1:-mongo3}

    log_warning "SCENARIO: Byzantine Failure - Simulating corrupted responses from $node"

    # This is simulated by temporarily making the node unreachable and then bringing it back
    # In a real scenario, you might inject corrupted data
    docker pause "$node"

    wait_for_recovery 15

    docker unpause "$node"

    log_info "Byzantine failure scenario ended"
}

# Scenario 10: Cascading Failures
scenario_cascading_failures() {
    log_warning "SCENARIO: Cascading Failures - Multiple sequential failures"

    log_info "Stage 1: CPU stress on mongo1"
    docker exec mongo1 bash -c "timeout 15s sh -c 'yes > /dev/null' &" || true
    sleep 5

    log_info "Stage 2: Network delay on mongo2"
    docker exec pumba pumba netem --duration 15s --interface eth0 delay --time 200 mongo2 &
    sleep 5

    log_info "Stage 3: Packet loss on mongo3"
    docker exec pumba pumba netem --duration 15s --interface eth0 loss --percent 30 mongo3 &

    wait_for_recovery 25

    log_info "Cascading failures scenario ended"
}

# Scenario 11: Rolling Restart
scenario_rolling_restart() {
    log_warning "SCENARIO: Rolling Restart - Restarting nodes one by one"

    for node in mongo1 mongo2 mongo3; do
        log_info "Restarting $node"
        docker restart "$node"
        wait_for_recovery 20
    done

    log_info "Rolling restart completed"
}

# Scenario 12: Primary Node Failure
scenario_primary_failure() {
    log_warning "SCENARIO: Primary Node Failure - Finding and killing primary"

    # Find the primary node (usually mongo1)
    PRIMARY=$(docker exec mongo1 mongosh --quiet --eval "rs.isMaster().primary" 2>/dev/null | grep -o "mongo[1-3]" || echo "mongo1")

    log_info "Primary node is: $PRIMARY"
    docker stop "$PRIMARY"

    wait_for_recovery 20

    docker start "$PRIMARY"
    log_info "Primary node restarted"
}

# Main menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "   MongoDB Chaos Engineering Scenarios   "
    echo "=========================================="
    echo "1.  Node Failure"
    echo "2.  Network Partition (Split-brain)"
    echo "3.  Network Delay (Latency)"
    echo "4.  Packet Loss"
    echo "5.  CPU Stress"
    echo "6.  Memory Stress"
    echo "7.  Disk I/O Stress"
    echo "8.  Clock Skew"
    echo "9.  Byzantine Failure"
    echo "10. Cascading Failures"
    echo "11. Rolling Restart"
    echo "12. Primary Node Failure"
    echo "13. Run ALL Scenarios (Sequential)"
    echo "0.  Exit"
    echo "=========================================="
}

# Run all scenarios
run_all_scenarios() {
    log_warning "Running ALL chaos scenarios sequentially..."

    scenario_node_failure mongo1
    wait_for_recovery 10

    scenario_network_delay 200 30 mongo2
    wait_for_recovery 10

    scenario_packet_loss 30 30 mongo3
    wait_for_recovery 10

    scenario_cpu_stress 30 mongo1
    wait_for_recovery 10

    scenario_memory_stress 30 mongo2
    wait_for_recovery 10

    scenario_disk_stress 30 mongo3
    wait_for_recovery 10

    scenario_rolling_restart
    wait_for_recovery 10

    scenario_primary_failure
    wait_for_recovery 10

    scenario_cascading_failures

    log_info "All chaos scenarios completed!"
}

# Interactive mode
if [ $# -eq 0 ]; then
    while true; do
        show_menu
        read -p "Select scenario (0-13): " choice

        case $choice in
            1) scenario_node_failure mongo1 ;;
            2) scenario_network_partition ;;
            3) scenario_network_delay 200 30 mongo2 ;;
            4) scenario_packet_loss 30 30 mongo3 ;;
            5) scenario_cpu_stress 30 mongo1 ;;
            6) scenario_memory_stress 30 mongo2 ;;
            7) scenario_disk_stress 30 mongo3 ;;
            8) scenario_clock_skew 300 mongo2 ;;
            9) scenario_byzantine_failure mongo3 ;;
            10) scenario_cascading_failures ;;
            11) scenario_rolling_restart ;;
            12) scenario_primary_failure ;;
            13) run_all_scenarios ;;
            0) log_info "Exiting..."; exit 0 ;;
            *) log_error "Invalid choice" ;;
        esac
    done
else
    # Command-line mode
    case $1 in
        node-failure) scenario_node_failure "${2:-mongo1}" ;;
        network-partition) scenario_network_partition ;;
        network-delay) scenario_network_delay "${2:-200}" "${3:-30}" "${4:-mongo2}" ;;
        packet-loss) scenario_packet_loss "${2:-30}" "${3:-30}" "${4:-mongo3}" ;;
        cpu-stress) scenario_cpu_stress "${2:-30}" "${3:-mongo1}" ;;
        memory-stress) scenario_memory_stress "${2:-30}" "${3:-mongo2}" ;;
        disk-stress) scenario_disk_stress "${2:-30}" "${3:-mongo3}" ;;
        clock-skew) scenario_clock_skew "${2:-300}" "${3:-mongo2}" ;;
        byzantine) scenario_byzantine_failure "${2:-mongo3}" ;;
        cascading) scenario_cascading_failures ;;
        rolling-restart) scenario_rolling_restart ;;
        primary-failure) scenario_primary_failure ;;
        all) run_all_scenarios ;;
        *)
            echo "Usage: $0 [scenario] [params...]"
            echo "Scenarios: node-failure, network-partition, network-delay, packet-loss,"
            echo "           cpu-stress, memory-stress, disk-stress, clock-skew, byzantine,"
            echo "           cascading, rolling-restart, primary-failure, all"
            exit 1
            ;;
    esac
fi
