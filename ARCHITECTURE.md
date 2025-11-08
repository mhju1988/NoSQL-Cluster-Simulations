# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Docker Host Machine                             │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │              Docker Network: mongo-cluster (172.25.0.0/16)        │ │
│  │                                                                   │ │
│  │  ┌─────────────────  MongoDB Replica Set  ─────────────────┐    │ │
│  │  │                                                           │    │ │
│  │  │   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │ │
│  │  │   │   mongo1     │      │   mongo2     │      │   mongo3     │  │ │
│  │  │   │  (Primary)   │◄────►│ (Secondary)  │◄────►│ (Secondary)  │  │ │
│  │  │   │              │      │              │      │              │  │ │
│  │  │   │ Port: 27017  │      │ Port: 27017  │      │ Port: 27017  │  │ │
│  │  │   │ CPU: 1 core  │      │ CPU: 1 core  │      │ CPU: 1 core  │  │ │
│  │  │   │ RAM: 512MB   │      │ RAM: 512MB   │      │ RAM: 512MB   │  │ │
│  │  │   └──────┬───────┘      └──────┬───────┘      └──────┬───────┘  │ │
│  │  │          │                     │                     │          │ │
│  │  └──────────┼─────────────────────┼─────────────────────┼──────────┘ │
│  │             │                     │                     │            │ │
│  │  ┌──────────▼─────────────────────▼─────────────────────▼──────────┐ │
│  │  │              MongoDB Exporters (Percona)                        │ │
│  │  │  ┌────────────┐    ┌────────────┐    ┌────────────┐           │ │
│  │  │  │ exporter1  │    │ exporter2  │    │ exporter3  │           │ │
│  │  │  │ Port: 9216 │    │ Port: 9216 │    │ Port: 9216 │           │ │
│  │  │  └─────┬──────┘    └─────┬──────┘    └─────┬──────┘           │ │
│  │  └────────┼───────────────────┼───────────────────┼────────────────┘ │
│  │           │                   │                   │                  │ │
│  │           └───────────────────┼───────────────────┘                  │ │
│  │                               │                                      │ │
│  │  ┌────────────────────────────▼──────────────────────────┐          │ │
│  │  │              Prometheus (Metrics Database)            │          │ │
│  │  │  • Scrape Interval: 15s                               │          │ │
│  │  │  • Retention: Default (15 days)                       │          │ │
│  │  │  • Alert Rules: 6 configured                          │          │ │
│  │  │  Port: 9090                                           │          │ │
│  │  └────────────────────────────┬──────────────────────────┘          │ │
│  │                               │                                      │ │
│  │  ┌────────────────────────────▼──────────────────────────┐          │ │
│  │  │              Grafana (Visualization)                  │          │ │
│  │  │  • Pre-configured MongoDB dashboard                   │          │ │
│  │  │  • Auto-provisioned datasource                        │          │ │
│  │  │  • 6 visualization panels                             │          │ │
│  │  │  Port: 3000 (admin/admin)                             │          │ │
│  │  └───────────────────────────────────────────────────────┘          │ │
│  │                                                                      │ │
│  │  ┌───────────────────────────────────────────────────────┐          │ │
│  │  │           Pumba (Network Chaos Engineering)           │          │ │
│  │  │  • Packet loss injection                              │          │ │
│  │  │  • Network delay/latency                              │          │ │
│  │  │  • Network partitions                                 │          │ │
│  │  │  • Requires privileged mode                           │          │ │
│  │  └───────────────────────────────────────────────────────┘          │ │
│  │                                                                      │ │
│  │  ┌───────────────────────────────────────────────────────┐          │ │
│  │  │         Test Orchestrator (Load & Automation)         │          │ │
│  │  │  • Python 3.11 with PyMongo                           │          │ │
│  │  │  • Load Generator                                     │          │ │
│  │  │  • Test Framework                                     │          │ │
│  │  │  • Docker API access                                  │          │ │
│  │  │  • Results export to /results                         │          │ │
│  │  └───────────────────────────────────────────────────────┘          │ │
│  │                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────  External Access Points  ────────────────────┐   │
│  │  MongoDB Primary:    localhost:27017                           │   │
│  │  MongoDB Secondary:  localhost:27018                           │   │
│  │  MongoDB Secondary:  localhost:27019                           │   │
│  │  Prometheus:         http://localhost:9090                     │   │
│  │  Grafana:            http://localhost:3000                     │   │
│  └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Normal Operation

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│    Client   │         │    Client   │         │    Client   │
│   (Write)   │         │    (Read)   │         │   (Read)    │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       │ Write Request         │ Read Request          │ Read Request
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│    mongo1    │───────►│    mongo2    │        │    mongo3    │
│  (Primary)   │        │ (Secondary)  │        │ (Secondary)  │
│              │───────►│              │        │              │
└──────────────┘  Repl  └──────────────┘        └──────────────┘
       │
       │ Write Response
       │ (w: majority)
       ▼
┌─────────────┐
│   Client    │
└─────────────┘
```

### 2. Monitoring Data Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   mongo1     │    │   mongo2     │    │   mongo3     │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │ MongoDB           │ MongoDB           │ MongoDB
       │ Metrics           │ Metrics           │ Metrics
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ exporter1    │    │ exporter2    │    │ exporter3    │
│ :9216        │    │ :9216        │    │ :9216        │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │ Scrape every 15s
                           ▼
                  ┌──────────────────┐
                  │   Prometheus     │
                  │   :9090          │
                  └────────┬─────────┘
                           │ PromQL queries
                           ▼
                  ┌──────────────────┐
                  │    Grafana       │
                  │    :3000         │
                  └──────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │   Dashboard      │
                  │   (Browser)      │
                  └──────────────────┘
```

### 3. Chaos Testing Flow

```
┌────────────────────────────────────────────────────────────┐
│                   Test Orchestrator                        │
│                                                            │
│  1. Start Load Generator                                   │
│     ├── Multi-threaded workers                             │
│     ├── Configurable read/write ratio                      │
│     └── Latency tracking (P50, P95, P99)                   │
│                                                            │
│  2. Inject Chaos (via chaos-scenarios.sh or Docker API)    │
│     ├── Stop container (node failure)                      │
│     ├── Network delay (via Pumba)                          │
│     ├── Packet loss (via Pumba)                            │
│     ├── Resource stress (CPU/Memory/Disk)                  │
│     └── Clock skew                                         │
│                                                            │
│  3. Observe Impact                                         │
│     ├── Operation success/failure rates                    │
│     ├── Latency changes                                    │
│     ├── Connection errors                                  │
│     └── Replication lag                                    │
│                                                            │
│  4. Recovery                                               │
│     ├── Restore container                                  │
│     ├── Heal network                                       │
│     └── Stop stress                                        │
│                                                            │
│  5. Export Results                                         │
│     └── JSON to /results/                                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   MongoDB Cluster      │
              │   (Under Test)         │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Prometheus           │
              │   (Metrics Collection) │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Grafana              │
              │   (Visualization)      │
              └────────────────────────┘
```

## Component Interactions

### Load Generator ↔ MongoDB

```
Load Generator                     MongoDB Cluster
─────────────                     ───────────────
[Thread 1]  ─┐
[Thread 2]  ─┤
[Thread 3]  ─┤── Write Ops ────►  [mongo1 (Primary)]
[Thread 4]  ─┤   (w: majority)         │
[Thread 5]  ─┤                         │ Replication
[Thread 6]  ─┤                         ▼
[Thread 7]  ─┤                    [mongo2, mongo3]
[Thread 8]  ─┤
[Thread 9]  ─┤── Read Ops ─────►  [mongo1/2/3 (NEAREST)]
[Thread 10] ─┘   (Read Pref)
```

### Chaos Injection Methods

**Method 1: Docker API**
```
Test Framework ──► Docker API ──► Stop/Start Container
                               ──► Pause/Unpause
                               ──► Restart
```

**Method 2: Pumba (Network Chaos)**
```
chaos-scenarios.sh ──► Pumba Container ──► tc (Traffic Control)
                                       ──► iptables rules
                                       ──► netem (network emulation)
```

**Method 3: In-Container Stress**
```
Docker Exec ──► Container Shell ──► CPU: yes > /dev/null
                                ──► Memory: dd if=/dev/zero
                                ──► Disk: dd writes
```

## Security Model

```
┌─────────────────────────────────────────────────────────┐
│                    Security Layers                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Network Isolation                                   │
│     • Custom Docker network (172.25.0.0/16)             │
│     • No direct external access                         │
│     • Port mapping only where needed                    │
│                                                         │
│  2. MongoDB Authentication                              │
│     • Username: admin                                   │
│     • Password: password123 (change in production!)     │
│     • Authentication database: admin                    │
│                                                         │
│  3. Grafana Authentication                              │
│     • Default: admin/admin                              │
│     • No sign-up allowed                                │
│     • Change on first login                             │
│                                                         │
│  4. Container Privileges                                │
│     • Pumba: privileged (required for network chaos)    │
│     • Test Orchestrator: Docker socket access           │
│     • Others: unprivileged                              │
│                                                         │
│  5. Volume Permissions                                  │
│     • Named volumes for persistence                     │
│     • Automatic ownership management                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Resource Allocation

```
Service              CPU Limit    Memory Limit    Disk
──────────────────   ─────────    ────────────    ────
mongo1               1.0 core     512 MB          Volume
mongo2               1.0 core     512 MB          Volume
mongo3               1.0 core     512 MB          Volume
mongodb-exporter1    (shared)     (shared)        None
mongodb-exporter2    (shared)     (shared)        None
mongodb-exporter3    (shared)     (shared)        None
prometheus           (shared)     (shared)        Volume
grafana              (shared)     (shared)        Volume
pumba                (shared)     (shared)        None
test-orchestrator    (shared)     (shared)        None

Total Reserved:      3.0 cores    1.5 GB
Total Recommended:   4.0 cores    8.0 GB          20 GB
```

## Network Topology

```
External Network                Docker Bridge Network (mongo-cluster)
────────────────                ──────────────────────────────────────

localhost:27017  ───┐
localhost:27018  ───┤
localhost:27019  ───┼──────►  [MongoDB Replica Set]
                    │          mongo1:27017
                    │          mongo2:27017
                    │          mongo3:27017
                    │
localhost:9090   ───┤──────►  [Prometheus]
                    │          prometheus:9090
                    │
localhost:3000   ───┘──────►  [Grafana]
                               grafana:3000

Internal Only:
  mongodb-exporter1:9216
  mongodb-exporter2:9216
  mongodb-exporter3:9216
```

## Failure Scenarios & Expected Behavior

| Scenario | What Happens | Recovery | Data Loss |
|----------|--------------|----------|-----------|
| **Primary Failure** | Elections starts, writes blocked | 10-15s | None (w:majority) |
| **Secondary Failure** | Reads still work, writes continue | Immediate | None |
| **2 Nodes Down** | Cluster read-only, no primary | Manual | None |
| **Network Partition** | Minority partition read-only | Auto on heal | None |
| **Packet Loss 30%** | Retries, slow operations | Immediate | None |
| **Network Delay 200ms** | +200ms latency, no failures | Immediate | None |
| **CPU Stress** | Slow operations, queue buildup | On stop | None |
| **Memory Pressure** | Swapping, very slow | On stop | None |
| **Clock Skew** | Election issues, replication lag | On sync | None |

## Monitoring Metrics

### MongoDB Metrics (Exported)

```
Category          Metric                           Description
────────────────  ──────────────────────────────   ─────────────────────────
Operations        mongodb_op_counters_total        Insert/query/update/delete
Latency           mongodb_op_latencies_latency     Read/write latency
Connections       mongodb_ss_connections           Current/available
Memory            mongodb_ss_mem_*                 Resident/virtual memory
Replication       mongodb_replset_member_*         State, lag, health
Network           mongodb_network_*                Bytes in/out
Storage           mongodb_ss_storage_*             Data/index size
```

### System Metrics (via cAdvisor - optional)

```
Category          Metric                           Description
────────────────  ──────────────────────────────   ─────────────────────────
CPU               container_cpu_usage_seconds      CPU time used
Memory            container_memory_usage_bytes     Memory usage
Network           container_network_*              Network I/O
Disk              container_fs_*                   Filesystem usage
```

## Deployment Patterns

### Development (Default)
- All-in-one docker-compose
- Shared resources
- Local storage
- Default passwords

### Testing
- Isolated networks per test
- Reproducible environments
- Automated cleanup
- Result archiving

### Research
- Extended retention periods
- Enhanced metrics collection
- Multiple test iterations
- Statistical analysis tools

### Production Simulation
- Realistic resource limits
- Production-grade monitoring
- Security hardening
- High availability configuration

---

**This architecture is designed for:**
- **Ease of use** - Single command deployment
- **Observability** - Comprehensive monitoring
- **Reproducibility** - Consistent test environments
- **Extensibility** - Easy to add components
- **Research** - Detailed metrics and analysis
