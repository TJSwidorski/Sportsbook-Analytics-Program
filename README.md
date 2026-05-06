# Axiom Sports

Sports-betting analytics pipeline — scrapes odds, models win probabilities, sizes bets with fractional Kelly, and publishes daily picks through a REST API and Next.js terminal UI at axiomsports.com.

> **For informational and entertainment purposes only. Not financial advice. 21+. Gambling may be illegal in your jurisdiction. Problem Gambling Helpline: 1-800-GAMBLER.**

---

## Local development

### Prerequisites

- Python 3.10+
- Node.js 18+

### Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install frontend dependencies
cd web && npm install && cd ..

# 3. Seed the SQLite cache (one-time, ~5-10 min)
py seed_db.py

# 4. Start everything (Flask API + Next.js frontend)
cd web && npm run dev:all
```

Open http://localhost:3000.

### Environment variables

Copy the example files and edit as needed:

```bash
copy .env.example .env
copy web\.env.example web\.env.local
```

Flask backend (`.env`):

| Variable | Default | Description |
|---|---|---|
| `API_HOST` | `0.0.0.0` | Bind address |
| `PORT` | `5000` | Listen port |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:3001` | CORS origins |

Next.js frontend (`web/.env.local`):

| Variable | Default | Description |
|---|---|---|
| `API_BASE_URL` | `http://localhost:5000` | Flask API base URL |

---

## Production deployment

The site is two pieces:

- **Frontend** — Next.js hosted on Netlify
- **Backend** — Flask + SQLite on a VPS (DigitalOcean Droplet recommended)

### Backend — DigitalOcean Droplet

**1. Create a droplet**

Ubuntu 24.04 LTS, Basic plan ($6/mo or higher). Add your SSH key.

**2. SSH in and install Python**

```bash
ssh root@<your-droplet-ip>
apt update && apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx
```

**3. Clone and install**

```bash
git clone https://github.com/<you>/Sportsbook-Analytics-Program.git /opt/axiom
cd /opt/axiom
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**4. Seed the cache**

```bash
source venv/bin/activate
python seed_db.py
```

**5. Create a systemd service**

```bash
cat > /etc/systemd/system/axiom.service << 'EOF'
[Unit]
Description=Axiom Sports Flask API
After=network.target

[Service]
User=root
WorkingDirectory=/opt/axiom
EnvironmentFile=/opt/axiom/.env
ExecStart=/opt/axiom/venv/bin/python api.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable axiom
systemctl start axiom
```

Create `/opt/axiom/.env`:

```
API_HOST=127.0.0.1
PORT=5000
ALLOWED_ORIGINS=https://axiomsports.com,https://www.axiomsports.com
```

**6. Point a subdomain at the droplet**

In your DNS panel (e.g. Cloudflare), add an A record: `api.axiomsports.com -> <droplet-ip>`.

**7. Configure nginx + SSL**

```bash
cat > /etc/nginx/sites-available/axiom << 'EOF'
server {
    listen 80;
    server_name api.axiomsports.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }
}
EOF

ln -s /etc/nginx/sites-available/axiom /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
certbot --nginx -d api.axiomsports.com
```

**8. Set up weekly model retraining (optional)**

```bash
crontab -e
# Add:
0 3 * * 0 cd /opt/axiom && source venv/bin/activate && python train_meta_model.py --walk-forward --force >> /var/log/axiom-train.log 2>&1
```

The Flask prefetch thread handles daily data updates automatically at startup -- no GitHub Actions or cron needed for real-time picks.

---

### Frontend — Netlify

**1. Import the repo**

Go to app.netlify.com -> Add new site -> Import from GitHub -> select this repo.

Build settings:
- Base directory: `web`
- Build command: `npm run build`
- Publish directory: `web/.next`

**2. Add the environment variable**

In Netlify: Site settings -> Environment variables -> Add:

```
API_BASE_URL = https://api.axiomsports.com
```

**3. Set the custom domain**

Netlify: Site settings -> Domain management -> Add custom domain -> `axiomsports.com`.

Add the CNAME/A records Netlify shows you in your DNS panel. Netlify provisions SSL automatically.

**4. Deploy**

Push to `main` -- Netlify builds and deploys automatically on every push.

---

## Architecture

```
SportsBookReview.com
  -> retrieve.py       (HTML scraper -> DataFrame)
  -> store.py          (SQLite at data/cache.db)
  -> package.py        (odds -> probabilities, scores -> labels)
  -> bayes.py          (Naive Bayes classifier)
  -> models.py         (logistic regression + logreg_v2 meta-gate)
  -> picks.py          (PickEngine: train + predict_all)
  -> runner.py         (daily orchestrator)
  -> prefetch.py       (background gap-fill + result settlement)
  -> api.py            (Flask REST API, port 5000)
  -> web/              (Next.js 15 -- Axiom Terminal)
```

Nine leagues (moneyline only): NBA, NHL, MLB, MLS, WNBA, NCAAB, NFL, NCAAF, CFL.

---

## Updating the model

After seeding new seasons:

```bash
# Retrain the meta-gate
py train_meta_model.py --walk-forward --force

# Reselect thresholds
py optimize_threshold.py --walk-forward --objective sharpe --save

# Refresh backtest history
py backtest_history.py --force

# Restart the service (picks up new pickles)
systemctl restart axiom
```

---

## Legal

For informational and entertainment purposes only. Nothing on this site constitutes financial, investment, or sports-betting advice. Past performance does not guarantee future results. Must be 21+ and comply with local gambling laws. If you or someone you know has a gambling problem, call 1-800-GAMBLER (1-800-426-2537) or visit ncpgambling.org.
