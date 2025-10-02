# 🐙 AI Defend - Distributed Security Monitoring Platform

AI Defend is an **enterprise-grade security monitoring platform** designed with a distributed "octopus" architecture. It separates the control plane (brain) from scanner agents (tentacles) to provide secure, scalable security monitoring across networks and systems.

## 🎯 Overview

AI Defend implements a modern security architecture where:
- **Control Plane (HEAD)**: Centralized management, AI/ML processing, and dashboard
- **Scanner Agents (TENTACLES)**: Distributed security scanners deployed across network segments
- **One-Way Data Flow**: Agents send data to the head, preventing lateral compromise
- **Kubernetes-Ready**: Designed for cloud-native deployment and horizontal scaling

### Architecture Philosophy

The platform is built on the principle of **isolation and containment**:
1. Scanner agents operate independently in isolated environments
2. Control plane receives and processes security data without direct agent control
3. Compromise of one component doesn't cascade to others
4. Scalable design supports enterprise-wide deployment

---

## 🏗️ Architecture

### Distributed "Octopus" Design

```
┌─────────────────────────────────────┐
│      CONTROL PLANE (HEAD)           │
│  ┌──────────────────────────────┐   │
│  │  Vue.js Dashboard            │   │
│  │  - Real-time monitoring      │   │
│  │  - Agent management          │   │
│  │  - Detection review          │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  FastAPI Backend             │   │
│  │  - Event processing          │   │
│  │  - Agent coordination        │   │
│  │  - AI/ML integration         │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  PostgreSQL + RabbitMQ       │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
              ▲
              │ One-way data flow
              │ (scan results only)
    ┌─────────┴─────────┐
    │                   │
┌───▼────┐         ┌────▼───┐
│ AGENT 1│         │ AGENT 2│
│ Network│         │  Host  │
│  Scan  │         │  Scan  │
└────────┘         └────────┘
```

### Key Components

**Control Plane**:
- **Frontend**: Modern Vue.js dashboard with real-time updates
- **Backend**: FastAPI with async processing
- **Database**: PostgreSQL for events and detections
- **Message Queue**: RabbitMQ for asynchronous task processing
- **AI/ML**: Model server for intelligent threat analysis

**Scanner Agents**:
- **Agent Client**: Auto-registration and heartbeat system
- **Security Scanners**: Nmap, Lynis, ClamAV, and more
- **Result Reporting**: Automatic event submission to control plane

---

## ✨ Features

### Security Monitoring
- **Network Scanning**: Discover hosts, services, and open ports
- **Security Auditing**: System hardening and compliance checks
- **Malware Detection**: File scanning and pattern matching
- **Event Correlation**: AI-powered threat detection
- **Real-time Alerts**: Immediate notification of security issues

### Agent Management
- **Auto-Registration**: Agents automatically connect to control plane
- **Health Monitoring**: Heartbeat-based agent status tracking
- **Task Assignment**: Distribute scans across agents
- **Load Balancing**: Intelligent workload distribution
- **Scalability**: Deploy unlimited agents across your infrastructure

### Dashboard & Reporting
- **Real-time Dashboard**: Live security status overview
- **Event Timeline**: Historical security event tracking
- **Detection Management**: Review and classify threats
- **Agent Monitoring**: View all registered scanner agents
- **Interactive Queries**: Ask AI about security events

### Enterprise Features
- **Kubernetes Support**: Deploy on K8s with provided manifests
- **Horizontal Scaling**: Scale agents based on workload
- **Multi-Region**: Deploy agents across geographic locations
- **API-First**: RESTful API for integration
- **Extensible**: Plugin architecture for custom scanners

---

## 📦 Getting Started

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM
- Modern web browser

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/g33knation/A_I_Defend.git
cd A_I_Defend
```

2. **Start all services**
```bash
docker-compose up -d --build
```

3. **Access the dashboard**
- Open your browser to `http://localhost:8001`
- Default view shows security dashboard with real-time stats

4. **View registered agents**
- Navigate to "Scanner Agents" (🐙 icon) in the sidebar
- See your scanner agent automatically registered and sending heartbeats

### First Scan

1. **Quick Scan from Dashboard**
   - Click "Run Quick Scan" button
   - System executes network scan and displays results
   - View detections in the "Detections" tab

2. **Assign Scan to Agent**
   - Go to "Scanner Agents" page
   - Click "Assign Scan" on an idle agent
   - Configure targets and scanners
   - Monitor scan execution in real-time

---

## 🎮 Usage

### Dashboard Navigation

**Main Dashboard** (`/`)
- Security overview with key metrics
- Total events, open detections, threats blocked
- Recent detections and events
- Quick scan functionality

**Events** (`/events`)
- Complete event timeline
- Filter by type and search
- Compact card view for easy scanning

**Detections** (`/detections`)
- Security threat detections
- Review and classify findings
- Mark as confirmed threat or false positive
- Run manual scans

**Scanner Agents** (`/agents`)
- View all registered agents
- Monitor agent health and status
- Assign scan tasks to specific agents
- Real-time heartbeat monitoring

**Ask AI** (`/ask`)
- Query the AI about security events
- Get intelligent analysis of threats
- Natural language security insights

### API Endpoints

**Agent Management**
```bash
# List all agents
GET /api/agents/

# Register new agent
POST /api/agents/register

# Agent heartbeat
POST /api/agents/heartbeat

# Assign scan to agent
POST /api/agents/{agent_id}/assign

# Check agent health
GET /api/agents/health/check
```

**Scan Management**
```bash
# Start a scan
POST /api/scans/start

# Get scan status
GET /api/scans/{scan_id}

# List all scans
GET /api/scans/
```

**Events & Detections**
```bash
# List events
GET /events

# Submit event
POST /events

# List detections
GET /detections

# Submit feedback
POST /feedback
```

---

## 🔒 Security Model

### Design Principles

1. **Isolation**: Scanner agents operate in isolated environments
2. **Least Privilege**: Minimal permissions for each component
3. **One-Way Flow**: Data flows from agents to control plane only
4. **Containment**: Compromise of one component doesn't affect others

### Data Flow

```
Scanner Agent → Scan Execution → Results
                                    ↓
                              POST /events
                                    ↓
                            Backend Processing
                                    ↓
                          Database Storage
                                    ↓
                          Dashboard Display
```

### Agent Security

- Agents run with capability-based security (NET_ADMIN, NET_RAW)
- Read-only access to host filesystems
- No credential storage in agents
- Assignment-based task model (pull, not push)

---

## 🚀 Deployment

### Docker Compose (Development)

```bash
# Start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Scale scanner agents
docker-compose up -d --scale scanner=3
```

### Kubernetes (Production)

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/scanner-deployment.yaml

# Scale agents
kubectl scale deployment scanner-agent -n ai-defend --replicas=10

# View agent pods
kubectl get pods -n ai-defend -l app=scanner

# View logs
kubectl logs -f deployment/scanner-agent -n ai-defend
```

### Environment Variables

**Backend**
- `DATABASE_URL`: PostgreSQL connection string
- `RABBITMQ_URL`: RabbitMQ connection string

**Scanner Agent**
- `API_URL`: Control plane API endpoint
- `SCAN_MODE`: Operation mode (network, local, hybrid)

---

## 📊 Monitoring

### Agent Health

Agents send heartbeats every 30 seconds. The control plane:
- Tracks last heartbeat timestamp
- Marks agents as stale after 5 minutes of inactivity
- Provides health check endpoint for monitoring

### Metrics

**Control Plane**
- Total registered agents
- Active scans
- Events processed per hour
- Detections created
- Agent health status

**Scanner Agents**
- Current status (idle, scanning, error)
- Scan completion rate
- Error rate
- Resource utilization

---

## 🛠️ Development

### Project Structure

```
A_I_Defend/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py      # Main application
│   │   └── routers/     # API routes
│   │       ├── scans.py # Scan management
│   │       └── agents.py# Agent management
│   └── Dockerfile
├── frontend/            # Vue.js dashboard
│   ├── src/
│   │   ├── views/       # Page components
│   │   ├── stores/      # State management
│   │   └── router/      # Routing
│   └── Dockerfile
├── scanners/            # Scanner agents
│   ├── agent_client.py  # Agent client
│   ├── linux/
│   │   └── security_scanner.py
│   └── Dockerfile
├── k8s/                 # Kubernetes manifests
│   └── scanner-deployment.yaml
└── docker-compose.yml   # Docker Compose config
```

### Adding Custom Scanners

1. Create scanner implementation in `scanners/`
2. Add scanner method to `SecurityScanner` class
3. Register scanner capability in agent client
4. Update frontend to support new scanner type

---

## 🤝 Contributing

This is an experimental platform for security research and education. Contributions are welcome!

### Guidelines
- Follow existing code structure
- Add tests for new features
- Update documentation
- Consider security implications

---

## 📝 License

This project is for educational and research purposes. Use responsibly and in accordance with applicable laws and regulations.

---

## ⚠️ Disclaimer

AI Defend is a security monitoring platform designed for authorized use only. Users are responsible for:
- Obtaining proper authorization before scanning networks
- Complying with applicable laws and regulations
- Using the platform ethically and responsibly
- Securing their deployment appropriately

The developers are not responsible for misuse of this platform.

---

## 🔮 Roadmap

- [ ] Enhanced AI/ML threat detection models
- [ ] Multi-tenancy support
- [ ] Advanced reporting and analytics
- [ ] Integration with SIEM platforms
- [ ] Automated response capabilities
- [ ] Mobile dashboard application
- [ ] Cloud provider integrations
- [ ] Compliance framework mapping

---

## 📚 Additional Documentation

- [Architecture Details](ARCHITECTURE.md) - Deep dive into system design
- [Scanner Documentation](scanners/README.md) - Scanner implementation guide
- [API Reference](http://localhost:8000/docs) - Interactive API documentation

---

## 💬 Support

For questions, issues, or contributions:
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share ideas

---

**Built with 🐙 by the AI Defend Team**
