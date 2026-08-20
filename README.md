# DINAS

**D**istributed **I**ntelligent **N**etwork **A**nalysis **S**ystem

A tool for discovering devices on your network, collecting data about them, and detecting when something looks wrong.

## What it does

DINAS scans your network to find devices, keeps track of what's there, collects performance data, and flags anything unusual. Think of it as a network monitoring system with anomaly detection.

**Right now it can:**
- Scan a network range to discover devices (ICMP ping, ARP)
- Store device info: hostname, IP, OS, services, interfaces
- Collect basic telemetry (latency, availability)
- Detect anomalies using statistical methods (z-score, thresholds)
- Auto-discover network topology (ARP neighbors, subnet adjacency, reachability, traceroute)
- Show everything in a web dashboard
- Run long tasks in background (discovery, telemetry, anomaly detection)
- Schedule periodic telemetry collection and anomaly detection

**What's still in progress:**
- The distributed agent (runs on remote machines to collect data)
- SNMP telemetry

## Setup

You need:
- Python 3.8+
- Git

### 1. Clone and install

```bash
git clone <repo-url>
cd Dinit

# Install Python dependencies
pip install -r backend/requirements.txt
```

### 2. Start the server

```bash
cd backend
python run.py
```

### 3. Open the dashboard

Go to **http://localhost:5000** in your browser.

That's it. One command starts everything — backend API and the web UI are served from the same place.

## How to use it

1. Go to **Discovery** page
2. Enter an IP range (like `192.168.1.0/24`)
3. Click **Start Scan**
4. Go to **Infrastructure** to see what was found
5. Check **Dashboard** for the overview

## Testing

```bash
cd backend
pip install pytest
pytest tests/ -v
```
