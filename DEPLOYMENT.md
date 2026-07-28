# 🚀 PersonaVault Deployment Guide

## Overview

This guide covers deploying PersonaVault in various environments, from development to production.

---

## 📋 Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **RAM** | 2GB | 4GB+ |
| **Storage** | 5GB | 10GB+ |
| **CPU** | 1 core | 2+ cores |
| **Docker** | 20.10+ | Latest |
| **Docker Compose** | 2.0+ | Latest |

---

## 🐳 Docker Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/personavault.git
cd personavault
```

### 2. Configure Environment

```bash
cp backend/.env.example .env
# Edit .env with your settings
```

### 3. Build and Run

```bash
docker-compose up -d
```

### 4. Verify Deployment

```bash
curl http://localhost:8000/health
```

---

## 🏗️ Production Checklist

### 🔒 Security
- [ ] SSL/TLS certificates configured (Let's Encrypt)
- [ ] Environment variables secured (not in .env files)
- [ ] Database passwords rotated
- [ ] API rate limiting enabled
- [ ] WebSocket authentication hardened

### 📊 Monitoring
- [ ] Prometheus metrics endpoint accessible
- [ ] Grafana dashboards configured
- [ ] Log aggregation (ELK/Loki)
- [ ] Alerting configured (PagerDuty/Slack)

### 💾 Data Management
- [ ] PostgreSQL (production) instead of SQLite
- [ ] Redis for rate limiting and caching
- [ ] Regular backups configured
- [ ] Backup retention policy defined

### 🚀 Performance
- [ ] Load testing completed
- [ ] CDN for static assets (if applicable)
- [ ] Database connection pooling tuned
- [ ] FAISS index persisted to shared storage

---

## 🏗️ Kubernetes Deployment

### Prerequisites
- Kubernetes 1.24+
- kubectl configured
- Helm 3+ (optional)

### Quick Start

```bash
# Apply secrets
kubectl create secret generic personavault-secrets \
  --from-literal=SECRET_KEY=<your-secret> \
  --from-literal=ENCRYPTION_KEY=<your-key>

# Deploy
kubectl apply -f k8s/
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Ollama not responding** | Check if Ollama is running: `ollama serve` |
| **Database connection failed** | Verify DATABASE_URL in .env |
| **Vector index corrupted** | Delete `storage/vector_metadata.pkl` and restart |
| **Disk full** | Run cleanup scripts: `./cleanup.sh` |

---

## 🆘 Support

For deployment issues, please open a GitHub issue or contact the team.