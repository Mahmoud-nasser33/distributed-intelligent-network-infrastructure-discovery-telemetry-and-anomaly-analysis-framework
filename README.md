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
- Show everything in a web dashboard

**What's still in progress:**
- The distributed agent (runs on remote machines to collect data)
- Background task processing
- SNMP telemetry
- Topology auto-discovery

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

## Pages

| Page | What it shows |
|------|--------------|
| Dashboard | Overview — device count, online/offline, open anomalies |
| Infrastructure | All discovered devices in a searchable table |
| Device Detail | One device — its info, services, interfaces, observations |
| Topology | Visual graph of device relationships (drag to move, scroll to zoom) |
| Telemetry | Performance charts and raw metrics |
| Anomalies | Detected issues — filter by severity and status |
| Agents | Registered collection agents and their status |
| Discovery | Run a network scan, see scan history |

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

## Project structure

```
Dinit/
├── backend/
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   ├── models/         # Database models
│   │   ├── discovery/      # Network scanning
│   │   ├── telemetry/      # Metric collection
│   │   ├── anomaly/        # Detection algorithms
│   │   └── topology/       # Graph building
│   ├── tests/              # 41 tests
│   └── run.py              # Start here
├── frontend/
│   └── static/             # HTML, CSS, JS (served by Flask)
│       ├── css/style.css
│       ├── js/app.js
│       ├── index.html      # Dashboard
│       └── *.html          # Other pages
└── README.md
```

## Tech

- **Backend:** Python, Flask, SQLAlchemy, SQLite
- **Frontend:** Plain HTML, CSS, JavaScript (no framework)
- **Scanning:** ICMP ping, ARP lookup, optional Nmap
- **Analysis:** Statistical anomaly detection (z-score, thresholds)

## License

MIT
