#!/bin/bash
# EC2 User Data — runs once on first boot
# Installs all dependencies and starts the Streamlit app as a systemd service

set -e
exec > /var/log/userdata.log 2>&1

# ── System packages ──────────────────────────────────────────────────────────
dnf update -y
dnf install -y python3 python3-pip git graphviz

# ── App setup ─────────────────────────────────────────────────────────────────
mkdir -p /opt/app
cd /opt/app

# Clone the app from GitHub
git clone https://github.com/BoopathiM9/aws-architecture-generator.git .

# Install Python dependencies
pip3 install -r requirements.txt

# ── Streamlit secrets for Bedrock credentials ─────────────────────────────────
mkdir -p /root/.streamlit
cat > /root/.streamlit/secrets.toml <<EOF
[aws]
AWS_ACCESS_KEY_ID     = "${aws_access_key_id}"
AWS_SECRET_ACCESS_KEY = "${aws_secret_access_key}"
AWS_DEFAULT_REGION    = "${aws_region}"
EOF

# ── Streamlit config (headless, correct port) ─────────────────────────────────
cat > /root/.streamlit/config.toml <<EOF
[server]
headless      = true
port          = 8501
enableCORS    = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
EOF

# ── Systemd service so app restarts on reboot ─────────────────────────────────
cat > /etc/systemd/system/${app_name}.service <<EOF
[Unit]
Description=AWS Architecture Generator (Streamlit)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/app
ExecStart=/usr/local/bin/streamlit run app.py
Restart=always
RestartSec=5
Environment=HOME=/root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${app_name}
systemctl start ${app_name}

echo "Bootstrap complete — Streamlit running on port 8501"
