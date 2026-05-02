# 🗜️ Visual Archive Permanent Hosting Plan

## Current State
- ✅ **Prototype MVP validated** — anchor_gallery.md exists with core symbols (124, 9, 17)
- ✅ **Local server running** on port 8000 → http://localhost:8000/anchor_gallery.md
- ⏳ **Permanent hosting needed** for external network access

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Home Server (External Access)                  │
│  ┌──────────────┐       ┌──────────────┐                        │
│  │   Nginx      │ ────▶ │   Gitea      │                        │
│  │  Reverse     │       │  Self-hosted │                        │
│  │  Proxy       │       │              │                        │
│  └──────────────┘       └──────────────┘                        │
│                                                                    │
│  Port 80/443 → Public                                            │
│  Port 3000+ → Visual Archive                                    │
└─────────────────────────────────────────────────────────────────┘

        ▲                        ▲
        │                        │
        ▼                        ▼
  Local Network         External Internet
  (Lan access)          (Remote access via port forward)
```

---

## 📦 Step 1: Push to GitHub/GitLab (Redundancy Layer)

### Why First?
- **Immediate availability** — get URL working while backend infrastructure deploys
- **Version control** — track all changes to Visual Archive content
- **Failover** — if Gitea fails, GitHub still serves content
- **Obsidian sync** — wikilinks work identically on both platforms

### Actions:
```bash
# Create git repo in ~/gematria/visual_archive/
cd ~/gematria/visual_archive/
git init
git add .
git commit -m "Initial Visual Archive prototype"
git remote add origin https://github.com/<your-username>/visual-archive.git
git push -u origin main
```

**Result:** `https://github.com/<your-username>/visual-archive/raw/main/output/anchor_gallery.md`

---

## 🔧 Step 2: Nginx Reverse Proxy Setup

### Option A: If You Have Home Server (e.g., old PC at home)

#### Install Nginx:
```bash
sudo pacman -S nginx --noconfirm
```

#### Create Nginx Config:
```bash
sudo nano /etc/nginx/sites-available/visual-archive
```

**Config content:**
```nginx
# Visual Archive Proxy Configuration

server {
    listen 80;
    server_name your-domain-or-ip.local;  # e.g., home.lan or 192.168.x.x
    
    # Gitea (if installed)
    location /gitea {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Visual Archive (serving from ~/gematria/visual_archive/output/)
    location / {
        alias /home/avalonas/gematria/visual_archive/output/;
        autoindex on;  # Show directory listings if needed
        
        # For markdown files with hotlinking
        types {
            application/x-markdown markdown;
            text/markdown markdown;
        }
        
        proxy_pass http://127.0.0.1:8000;  # Fallback to local server
    }
}
```

#### Enable & Start:
```bash
sudo ln -s /etc/nginx/sites-available/visual-archive /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Result:** `http://your-domain-or-ip.local/anchor_gallery.md`

---

### Option B: Pure Local Server with Public Access (Alternative)

If you want to keep using the current local server but make it accessible from outside your network, you can set up:

#### Install Portainer for Docker Management:
```bash
# Via ArchUser Repository
sudo pacman -S docker --noconfirm
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Add port forwarding (check if port 80/8080 is free)
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8000
```

Then use a VPS or tunneling service like:
- **Cloudflare Tunnel:** `cloudflared tunnel --url http://localhost:8000`
- **Ngrok (free tier):** `ngrok http 8000`
- **Tailscale:** Zero-config access from any device on your network

---

## 🐳 Step 3: Gitea Self-Hosted Installation

### Option A: Direct Binary (Simpler, No Docker)

#### Download Full Gitea:
```bash
# Get the official latest version
wget -O /tmp/gitea.tar.gz \
  "https://dl.gitea.com/gitea/1.23.0/gitea-1.23.0.linux-amd64.tar.gz"

# Extract
tar -xzf /tmp/gitea.tar.gz -C /tmp/

# Move to installation directory
sudo mv /tmp/gitea-1.23.0 /opt/gitea
```

#### Configure Database:
```bash
cd /opt/gitea
./gitea web --init-db
# Follow prompts (admin email, password)
```

### Option B: Docker (Recommended for Production)

#### Create Docker Compose:
```bash
mkdir -p ~/gematria/visual_archive/docker
cd ~/gematria/visual_archive/docker

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mysql:
    image: gitea/gitea-mysql
    environment:
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - ./mysql:/var/lib/mysql
    ports:
      - "3306:3306"
    
  gitea:
    image: gitea/gitea:latest
    environment:
      GITEA__database:
        TYPE: mysql
        DBNAME: ${DB_NAME}
        USERNAME: ${DB_USER}
        PASSWORD: ${DB_PASSWORD}
        ROOTPASSWORD: ${DB_ROOT_PASSWORD}
      GITEA__server:
        DOMAIN: gitea.local
        ROOT_URL: http://gitea.local/
        HTTP_PORT: 3000
    volumes:
      - ./gitea:/data
    ports:
      - "3000:3000"
    depends_on:
      - mysql

EOF
```

#### Environment Variables:
```bash
export DB_NAME=gitea
export DB_USER=gitea
export DB_PASSWORD=your_secure_password
export DB_ROOT_PASSWORD=root_password
```

#### Start with Docker:
```bash
docker-compose up -d
```

---

## 🔗 Integration Points

### For Visual Archive Content:

1. **Git-based:**
   ```bash
   # Push Visual Archive updates to Git repo
   cd ~/gematria/visual_archive
   git add .
   git commit -m "Update Visual Archive patterns"
   git push origin main
   ```

2. **Obsidian Sync (if using Gitea):**
   - Clone Gitea as remote: `git remote add gitea ssh://gitea.local:3000/visual-archive`
   - Configure Obsidian sync to pull from Gitea Git repo

3. **Real-time updates:**
   - Keep current local server running for live preview
   - Nginx proxy can route requests accordingly

---

## 📋 Verification Checklist

- [ ] GitHub/GitLab repo created and pushed
- [ ] Nginx reverse proxy installed and configured
- [ ] Port forwarding set up (or tunneling service active)
- [ ] Gitea installed (Docker or binary) with admin account
- [ ] Test access from external device (phone, another computer)
- [ ] Create Visual Archive Git repo on Gitea and push content

---

## 🎯 Recommended Implementation Order

### Phase 1: Quick Win (Today)
```bash
# Push to GitHub for immediate URL
cd ~/gematria/visual_archive
git init && git add . && git commit -m "Initial"
git remote add origin https://github.com/<you>/visual-archive.git
git push -u origin main

# Your temporary external URL:
# https://github.com/<you>/visual-archive/raw/main/output/anchor_gallery.md
```

### Phase 2: Permanent Infrastructure (Weekend)
- [ ] Set up home server with Nginx
- [ ] Deploy Gitea via Docker (most reliable)
- [ ] Configure domain/port forwarding
- [ ] Migrate Visual Archive to Gitea Git repo

### Phase 3: Long-term Maintenance (Ongoing)
- Push Visual Archive updates → GitHub/Gitea automatically deploy
- Local server for live preview while backend syncs
- Backup schedule for all data

---

## 💡 Additional Recommendations

1. **SSL/HTTPS:** Use Let's Encrypt via Certbot:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.local
   ```

2. **Firewall Rules:** Only allow ports 80, 443 (and Gitea port if direct access)
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. **Database Backup:** Set up cron job for MySQL backups to external storage

4. **Monitoring:** Consider Prometheus/Grafana for server health monitoring

---

## 📞 Support Resources

- **Gitea Docs:** https://docs.gitea.com/
- **Nginx Wiki:** https://nginx.org/en/docs/wiki.html
- **Reverse Proxy Tutorial:** https://nginx.com/resources/nginx-web-proxy-tutorial/

---

**Status:** Ready for implementation  
**Next Action:** Choose implementation path (GitHub push + Nginx, or pure Docker setup)
