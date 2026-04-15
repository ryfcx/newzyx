# Deploying Newzyx to a Linux Server

## Prerequisites

- Ubuntu 22.04+ with SSH access
- Python 3.10+
- 1 GB RAM, 5 GB disk

## 1. Copy the Project

```bash
rsync -avz --exclude='venv/' --exclude='data/' --exclude='website/*.html' \
  --exclude='website/*.mp3' \
  ~/Desktop/Newzyx/ user@server:~/Newzyx/
```

## 2. Set Up Python

```bash
cd ~/Newzyx
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configure Secrets

```bash
cp .env.example .env
nano .env  # Fill in all API keys
```

## 4. Create Directories

```bash
mkdir -p data website alt
```

## 5. Test

```bash
source venv/bin/activate
python3 -c "from pipeline import db, collect, extract, process, episode, tts, upload, rss; print('OK')"
python3 run_once.py
```

## 6. Run as a Service (systemd)

```bash
sudo nano /etc/systemd/system/newzyx.service
```

```ini
[Unit]
Description=Newzyx Daily Podcast Pipeline
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/Newzyx
ExecStart=/home/your-user/Newzyx/venv/bin/python3 main.py
Restart=on-failure
RestartSec=60
StandardOutput=append:/home/your-user/Newzyx/logs/stdout.log
StandardError=append:/home/your-user/Newzyx/logs/stderr.log

[Install]
WantedBy=multi-user.target
```

```bash
mkdir -p ~/Newzyx/logs
sudo systemctl daemon-reload
sudo systemctl enable newzyx
sudo systemctl start newzyx
```

## Useful Commands

```bash
sudo systemctl status newzyx           # Check status
sudo journalctl -u newzyx -f           # Live logs
sudo systemctl restart newzyx          # Restart after code changes
sudo systemctl stop newzyx             # Stop
```

## Schedule

The scheduler in `main.py` runs at **5:02 AM server time** daily. Set your timezone:

```bash
timedatectl                                    # Check
sudo timedatectl set-timezone America/New_York  # Change
```

## Updating Code

```bash
# From your Mac:
rsync -avz --exclude='venv/' --exclude='data/' --exclude='website/' --exclude='alt/' \
  ~/Desktop/Newzyx/ user@server:~/Newzyx/

# On the server:
sudo systemctl restart newzyx
```
