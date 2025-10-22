# AI Defend - Distributed Security Monitoring Platform

Enterprise-grade security monitoring platform with distributed architecture for scalable network and system defense.

## Overview

AI Defend implements a distributed security architecture:
- **Control Plane**: Centralized management, AI/ML processing, and dashboard
- **Scanner Agents**: Distributed security scanners deployed across network segments
- **One-Way Data Flow**: Agents send data to control plane, preventing lateral compromise
- **Cloud-Native**: Kubernetes-ready for enterprise deployment

### Architecture Philosophy

Built on principles of **isolation and containment**:
1. Scanner agents operate independently in isolated environments
2. Control plane processes security data without direct agent control
3. Component compromise doesn't cascade to others
4. Horizontal scaling supports enterprise-wide deployment

---

## Features

### Security Monitoring
- **Network Scanning**: Host discovery, service enumeration, port analysis
- **Security Auditing**: System hardening and compliance validation
- **Malware Detection**: File scanning and pattern matching
- **Event Correlation**: AI-powered threat analysis
- **Real-time Alerts**: Immediate security event notification

### Agent Management
- **Auto-Registration**: Agents connect automatically to control plane
- **Health Monitoring**: Heartbeat-based status tracking
- **Task Distribution**: Intelligent scan assignment across agents
- **Load Balancing**: Workload optimization
- **Scalability**: Deploy agents across infrastructure segments

### Dashboard & Reporting
- **Live Monitoring**: Real-time security status
- **Event Timeline**: Historical security event tracking
- **Detection Management**: Threat review and classification
- **Agent Monitoring**: Registered scanner agent visibility
- **AI Assistant**: Natural language security queries

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM recommended
- Modern web browser

### Quick Start

```bash
# Clone repository
git clone https://github.com/g33knation/A_I_Defend.git
cd A_I_Defend

# Start all services
docker-compose up -d --build

# Access dashboard
# Navigate to http://localhost:8001
```

### Initial Configuration

1. Access the web dashboard
2. Navigate to "Scanner Agents" to view registered agents
3. Assign scan tasks to agents via the UI
4. Monitor results in "Detections" and "Events" views

---

## Usage

### Dashboard Navigation

- **Events**: Complete event timeline with filtering
- **Detections**: Security threat review and classification
- **Scanner Agents**: Agent health monitoring and task assignment
- **Ask AI**: Natural language security analysis

### Scanner Capabilities

**Network Intelligence**
- Port scanning and service discovery
- Traffic analysis and protocol detection
- Network mapping and topology discovery
- DNS enumeration

**Security Auditing**
- System configuration analysis
- Compliance validation
- Rootkit detection
- Security baseline verification

**Malware Detection**
- File signature scanning
- Pattern matching
- Behavioral analysis

---

## Security Model

### Design Principles

1. **Isolation**: Agents operate in isolated environments
2. **Least Privilege**: Minimal permissions per component
3. **Unidirectional Flow**: Data flows from agents to control plane only
4. **Containment**: Component compromise isolation

### Agent Security

- Capability-based security model
- Read-only filesystem access where applicable
- No credential storage in agents
- Pull-based task assignment model

### Deployment Security

- Change default credentials immediately
- Use TLS for production deployments
- Implement network segmentation
- Regular security updates
- Monitor agent activity logs
- Restrict API access

---

## Deployment

### Docker Compose

```bash
# Start services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Kubernetes

```bash
# Deploy agents
kubectl apply -f k8s/scanner-deployment.yaml

# Scale deployment
kubectl scale deployment scanner-agent -n ai-defend --replicas=10
```

### Production Considerations

- Configure persistent storage for PostgreSQL
- Implement backup strategies
- Use secrets management for credentials
- Enable TLS/SSL for all communications
- Configure resource limits
- Implement monitoring and alerting
- Regular security audits

---

## Monitoring

### Health Checks

- Agents send heartbeats every 30 seconds
- Control plane tracks agent status
- Stale detection after 5 minutes of inactivity

### Metrics

**Control Plane**
- Registered agent count
- Active scan count
- Event processing rate
- Detection creation rate

**Agents**
- Current status
- Scan completion rate
- Error rate

---

## Development

### Project Structure

```
A_I_Defend/
├── backend/              # FastAPI control plane
├── frontend/             # Vue.js dashboard
├── scanners/             # Scanner agent implementations
├── k8s/                  # Kubernetes manifests
└── docker-compose.yml    # Development orchestration
```

### Extending Functionality

1. Implement scanner in `scanners/` directory
2. Register capability in agent client
3. Update frontend for new scanner type
4. Test thoroughly before deployment

---

## Legal & Compliance

### Authorization Requirements

**You must have explicit authorization before scanning any network or system.**

- Obtain written permission for all scan targets
- Comply with organizational security policies
- Follow applicable laws and regulations
- Document all scanning activities
- Maintain audit logs

### Responsible Use

- Only scan authorized networks and systems
- Respect privacy and data protection laws
- Use appropriate scan intensity
- Schedule scans during approved windows
- Report vulnerabilities responsibly

### Disclaimer

This platform is for authorized security monitoring only. Users are solely responsible for:
- Obtaining proper authorization
- Legal compliance
- Ethical use
- Deployment security

Developers assume no liability for misuse.

---

## Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: See project wiki
- **Security**: Report vulnerabilities privately

---

**AI Defend Team**
