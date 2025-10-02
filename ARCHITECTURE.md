# AI Defend - Distributed Security Architecture

## 🐙 Octopus Architecture

AI Defend implements a distributed "octopus" architecture where the **HEAD** (control plane) manages multiple **TENTACLES** (scanner agents) for comprehensive security monitoring.

```
                    ┌─────────────────────────────────┐
                    │      HEAD (Control Plane)       │
                    │  ┌──────────────────────────┐   │
                    │  │  Frontend Dashboard      │   │
                    │  └──────────────────────────┘   │
                    │  ┌──────────────────────────┐   │
                    │  │  Backend API             │   │
                    │  │  - Agent Management      │   │
                    │  │  - Event Processing      │   │
                    │  │  - AI/ML Models          │   │
                    │  └──────────────────────────┘   │
                    │  ┌──────────────────────────┐   │
                    │  │  PostgreSQL Database     │   │
                    │  └──────────────────────────┘   │
                    └─────────────────────────────────┘
                                  ▲
                                  │ One-way data flow
                                  │ (scan results only)
                    ┌─────────────┴─────────────┐
                    │                           │
          ┌─────────▼─────────┐       ┌────────▼────────┐
          │  TENTACLE 1       │       │  TENTACLE 2     │
          │  (Scanner Agent)  │       │  (Scanner Agent)│
          │  ┌──────────────┐ │       │  ┌────────────┐ │
          │  │ Nmap         │ │       │  │ ClamAV     │ │
          │  │ Lynis        │ │       │  │ YARA       │ │
          │  │ Network Scan │ │       │  │ File Scan  │ │
          │  └──────────────┘ │       │  └────────────┘ │
          │  Target: 10.0.0.0 │       │  Target: Host  │
          └───────────────────┘       └─────────────────┘
```

## 🎯 Key Features

### 1. **Agent Registration**
- Agents automatically register with the control plane on startup
- Provide capabilities (nmap, lynis, clamav, etc.)
- Send periodic heartbeats to maintain connection

### 2. **Target Assignment**
- Control plane assigns scan targets to specific agents
- Load balancing across multiple agents
- Priority-based task scheduling

### 3. **One-Way Communication**
- Agents only send data TO the head (never receive commands directly)
- Results flow: Agent → Backend → Database → Dashboard
- Prevents compromise of control plane from affecting agents

### 4. **Health Monitoring**
- Real-time agent status tracking
- Automatic detection of stale/offline agents
- Heartbeat-based health checks

### 5. **Kubernetes Ready**
- Deploy agents as DaemonSets across cluster nodes
- Horizontal scaling of scanner agents
- Network policy enforcement for security

## 📋 Components

### Control Plane (HEAD)

**Backend API** (`/api/agents/`)
- `POST /register` - Agent registration
- `POST /heartbeat` - Agent health check
- `GET /` - List all agents
- `POST /{agent_id}/assign` - Assign scan task
- `GET /health/check` - Check agent health

**Frontend Dashboard** (`/agents`)
- View all registered agents
- Monitor agent status in real-time
- Assign scan tasks to specific agents
- View agent capabilities and metrics

### Scanner Agents (TENTACLES)

**Agent Client** (`agent_client.py`)
- Auto-registration with control plane
- Heartbeat loop (every 30 seconds)
- Assignment processing
- Result reporting

**Scanners**
- Nmap - Network scanning
- Lynis - Security auditing
- ClamAV - Antivirus scanning
- YARA - Pattern matching
- Suricata - IDS/IPS

## 🚀 Deployment

### Docker Compose (Development)

```bash
# Build and start all services
docker-compose up -d --build

# View agent logs
docker logs scanner -f

# Check agent status
curl http://localhost:8000/api/agents/
```

### Kubernetes (Production)

```bash
# Create namespace
kubectl apply -f k8s/scanner-deployment.yaml

# Scale agents
kubectl scale deployment scanner-agent -n ai-defend --replicas=5

# View agents
kubectl get pods -n ai-defend -l app=scanner

# Assign scan via API
curl -X POST http://backend-service:8000/api/agents/{agent_id}/assign \
  -H "Content-Type: application/json" \
  -d '{
    "targets": ["10.0.0.0/24"],
    "scanners": ["nmap"],
    "config": {"ports": "1-1000"}
  }'
```

## 🔒 Security Model

### Isolation Principles

1. **Network Segmentation**
   - Agents run in isolated network segments
   - Only outbound connections to control plane
   - No direct agent-to-agent communication

2. **Least Privilege**
   - Agents run with minimal required permissions
   - Read-only access to host filesystems
   - Capability-based security (NET_ADMIN, NET_RAW only when needed)

3. **Data Flow Control**
   - Unidirectional data flow (Agent → Head)
   - No command execution from control plane
   - Assignment-based task model (pull, not push)

4. **Compromise Containment**
   - If agent is compromised, control plane remains secure
   - If control plane is compromised, agents continue operating independently
   - No credentials or secrets stored in agents

## 📊 Monitoring & Observability

### Agent Metrics
- Status (idle, scanning, error)
- Last heartbeat timestamp
- Current task assignment
- Scan results count
- Error rate

### Control Plane Metrics
- Total registered agents
- Active scans
- Events processed
- Detections created
- Agent health status

## 🔄 Workflow Example

1. **Agent Startup**
   ```
   Scanner Agent → Register with Control Plane
   Scanner Agent → Start heartbeat loop
   ```

2. **Scan Assignment**
   ```
   User → Dashboard → Assign scan to Agent
   Control Plane → Store assignment
   Agent → Heartbeat → Receive assignment
   ```

3. **Scan Execution**
   ```
   Agent → Execute scan (nmap, lynis, etc.)
   Agent → Post results to /events endpoint
   Backend → Create detections
   Dashboard → Display results
   ```

4. **Health Monitoring**
   ```
   Agent → Send heartbeat every 30s
   Control Plane → Track last heartbeat
   Control Plane → Mark stale if >5min
   ```

## 🎓 Best Practices

1. **Agent Deployment**
   - Deploy one agent per network segment
   - Use DaemonSets in Kubernetes for node coverage
   - Configure appropriate scan targets per agent

2. **Target Assignment**
   - Assign network ranges based on agent location
   - Use priority for critical scans
   - Balance load across agents

3. **Monitoring**
   - Set up alerts for stale agents
   - Monitor scan completion rates
   - Track detection trends

4. **Scaling**
   - Add agents for new network segments
   - Scale horizontally for increased coverage
   - Use Kubernetes HPA for dynamic scaling

## 🔮 Future Enhancements

- [ ] Agent authentication with mutual TLS
- [ ] Encrypted communication channels
- [ ] Advanced load balancing algorithms
- [ ] Agent capability negotiation
- [ ] Distributed scan coordination
- [ ] Real-time agent metrics streaming
- [ ] Agent auto-discovery
- [ ] Multi-region deployment support
