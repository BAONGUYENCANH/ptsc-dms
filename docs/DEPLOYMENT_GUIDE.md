# DigitalOcean Deployment Guide

Chi tiết từng bước để deploy PTSC DMS lên DigitalOcean với GitHub Student Pack.

## 📋 Chuẩn bị

### 1. GitHub Student Pack

1. Đăng ký tại: https://education.github.com/pack
2. Verify với email sinh viên (.edu)
3. Nhận $200 credit DigitalOcean (2 năm)

### 2. DigitalOcean Account

1. Tạo account: https://www.digitalocean.com/
2. Link với GitHub Student Pack
3. Verify credit đã được add

---

## 🚀 Method 1: App Platform (Recommended)

**Ưu điểm:**
- ✅ Tự động build & deploy
- ✅ HTTPS miễn phí
- ✅ Auto-scaling
- ✅ Zero downtime deployments
- ✅ Monitoring built-in

**Chi phí:** $12/month (hoặc free với credit)

### Bước 1: Push code lên GitHub

```bash
cd "E:\Laptrinh\AddIns\PHIÊN BẢN OK NHẤT TỪNG CÓ\PTSC_PROJECT\Deploy Github"

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: PTSC DMS for DigitalOcean"

# Add remote
git remote add origin https://github.com/BAONGUYENCANH/ptsc-dms.git

# Push
git push -u origin main
```

### Bước 2: Create App trên DigitalOcean

1. **Go to App Platform:**
   https://cloud.digitalocean.com/apps

2. **Click "Create App"**

3. **Choose GitHub:**
   - Select "GitHub"
   - Authorize DigitalOcean
   - Choose repository: `BAONGUYENCANH/ptsc-dms`
   - Branch: `main`

4. **Configure Resources:**

   **Backend Service:**
   ```
   Name: ptsc-backend
   Type: Web Service
   
   Source:
   - Source Directory: /backend
   
   Build Phase:
   - Build Command: pip install -r requirements.txt
   
   Run Phase:
   - Run Command: gunicorn --bind :$PORT app:app
   
   Environment Variables:
   - FLASK_ENV = production
   - PORT = 8080
   
   HTTP Port: 8080
   HTTP Request Routes: /api
   ```

   **Frontend Static Site:**
   ```
   Name: ptsc-frontend
   Type: Static Site
   
   Source:
   - Source Directory: /frontend
   
   Build Phase:
   - Build Command: npm install && npm run build
   - Output Directory: dist
   
   HTTP Request Routes: /
   ```

5. **Choose Plan:**
   - Basic: $5/month for backend
   - Starter: Free for frontend
   - **Total: ~$5-12/month**

6. **Add Environment Variables:**
   
   Backend:
   ```env
   FLASK_ENV=production
   DATABASE_PATH=/data/project_data.db
   UPLOAD_FOLDER=/tmp/uploads
   ```

   Frontend (build time):
   ```env
   VITE_API_URL=https://ptsc-backend-xxx.ondigitalocean.app/api
   ```

7. **Click "Create Resources"**

### Bước 3: Wait for Deploy

- Deployment takes ~5-10 minutes
- Check build logs for errors
- Once complete, you'll get URLs:
  - Frontend: `https://ptsc-frontend-xxx.ondigitalocean.app`
  - Backend: `https://ptsc-backend-xxx.ondigitalocean.app`

### Bước 4: Test Deployment

```bash
# Test backend health
curl https://ptsc-backend-xxx.ondigitalocean.app/api/health

# Expected:
# {"status":"healthy","timestamp":"...","database":false}
```

Open frontend URL in browser and test:
1. Upload Excel file
2. View dashboard
3. Check charts

---

## 🖥️ Method 2: Droplet (Manual)

**Ưu điểm:**
- ✅ Full control
- ✅ Can install any software
- ✅ Lower cost for small apps

**Chi phí:** $6/month

### Bước 1: Create Droplet

1. Go to: https://cloud.digitalocean.com/droplets
2. Click **"Create Droplet"**
3. Choose:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic ($6/month, 1GB RAM)
   - **Datacenter:** Singapore (closest to Vietnam)
   - **Authentication:** SSH key (recommended)
4. Click **"Create Droplet"**
5. Note the IP address

### Bước 2: Initial Setup

SSH into droplet:

```bash
ssh root@YOUR_DROPLET_IP
```

Update system:

```bash
# Update packages
apt update && apt upgrade -y

# Install essentials
apt install -y git curl wget vim

# Create non-root user
adduser ptsc
usermod -aG sudo ptsc

# Switch to new user
su - ptsc
```

### Bước 3: Install Dependencies

```bash
# Install Python
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
sudo apt install -y nginx

# Install certbot for SSL
sudo apt install -y certbot python3-certbot-nginx

# Verify installations
python3 --version
node --version
npm --version
nginx -v
```

### Bước 4: Clone Repository

```bash
cd /var/www
sudo mkdir ptsc-dms
sudo chown ptsc:ptsc ptsc-dms
cd ptsc-dms

git clone https://github.com/BAONGUYENCANH/ptsc-dms.git .
```

### Bước 5: Setup Backend

```bash
cd /var/www/ptsc-dms/backend

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env
# Edit with your settings

# Test run
python app.py
# Press Ctrl+C to stop
```

Create systemd service:

```bash
sudo nano /etc/systemd/system/ptsc-backend.service
```

Add content:

```ini
[Unit]
Description=PTSC Backend API
After=network.target

[Service]
User=ptsc
Group=ptsc
WorkingDirectory=/var/www/ptsc-dms/backend
Environment="PATH=/var/www/ptsc-dms/backend/venv/bin"
ExecStart=/var/www/ptsc-dms/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ptsc-backend
sudo systemctl start ptsc-backend
sudo systemctl status ptsc-backend
```

### Bước 6: Setup Frontend

```bash
cd /var/www/ptsc-dms/frontend

# Create .env.production
cp .env.example .env.production
nano .env.production
# Set VITE_API_URL to your domain or IP

# Install dependencies
npm install

# Build
npm run build

# Copy to web root
sudo mkdir -p /var/www/html/ptsc
sudo cp -r dist/* /var/www/html/ptsc/
```

### Bước 7: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/ptsc-dms
```

Add content:

```nginx
server {
    listen 80;
    server_name YOUR_DROPLET_IP;  # or your domain

    # Frontend
    location / {
        root /var/www/html/ptsc;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeouts for file uploads
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }

    # Max upload size
    client_max_body_size 20M;
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/ptsc-dms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Bước 8: Firewall Setup

```bash
# Enable UFW
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Check status
sudo ufw status
```

### Bước 9: Setup SSL (Optional)

If you have a domain:

```bash
# Point domain to droplet IP first
# Then run certbot

sudo certbot --nginx -d your-domain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

### Bước 10: Test Deployment

```bash
# Test backend
curl http://YOUR_DROPLET_IP/api/health

# Test frontend
curl http://YOUR_DROPLET_IP/
```

Open browser: `http://YOUR_DROPLET_IP`

---

## 🔧 Post-Deployment

### Database Persistence (App Platform)

Create persistent volume:

1. App Platform → Settings → Add Component
2. Choose "Database" → "Managed Database"
3. Or use Spaces (S3-compatible) for SQLite file

### Monitoring

**App Platform:**
- Built-in metrics dashboard
- View logs in real-time
- Set up alerts

**Droplet:**
Install monitoring agent:

```bash
curl -sSL https://repos.insights.digitalocean.com/install.sh | sudo bash
```

### Backups

**Database Backup Script:**

```bash
# Create backup script
nano /var/www/ptsc-dms/backend/backup.sh
```

Content:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/ptsc"
mkdir -p $BACKUP_DIR

# Backup database
cp /var/www/ptsc-dms/backend/project_data.db $BACKUP_DIR/db_$DATE.db

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.db" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable and add to cron:

```bash
chmod +x /var/www/ptsc-dms/backend/backup.sh

# Add to crontab
crontab -e
# Add line:
0 2 * * * /var/www/ptsc-dms/backend/backup.sh
```

### Auto-Deploy on Push

**App Platform:** Already automatic!

**Droplet:** Setup webhook or GitHub Actions

---

## 📊 Monitoring & Maintenance

### Check Service Status

```bash
# Backend
sudo systemctl status ptsc-backend

# Nginx
sudo systemctl status nginx

# View logs
sudo journalctl -u ptsc-backend -f
sudo tail -f /var/log/nginx/error.log
```

### Update Application

```bash
cd /var/www/ptsc-dms
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ptsc-backend

# Update frontend
cd ../frontend
npm install
npm run build
sudo cp -r dist/* /var/www/html/ptsc/
```

---

## 💰 Cost Breakdown

### With GitHub Student Pack ($200 credit)

**App Platform:**
- Backend: $5-12/month
- Frontend: Free
- Database (optional): $15/month
- **Total: $5-27/month** (covered by credit for ~8-40 months)

**Droplet:**
- Basic Droplet: $6/month
- Managed Database (optional): $15/month
- Domain (optional): $12/year
- **Total: $6-21/month** (covered by credit for ~10-33 months)

---

## 🐛 Troubleshooting

### Issue: Build Failed

**App Platform:**
- Check build logs
- Verify package.json and requirements.txt
- Check Node/Python versions

**Droplet:**
```bash
# Check backend logs
sudo journalctl -u ptsc-backend -n 100

# Test backend manually
cd /var/www/ptsc-dms/backend
source venv/bin/activate
python app.py
```

### Issue: 502 Bad Gateway

```bash
# Check if backend is running
sudo systemctl status ptsc-backend

# Check Nginx config
sudo nginx -t

# Restart services
sudo systemctl restart ptsc-backend
sudo systemctl restart nginx
```

### Issue: Can't Upload Files

```bash
# Check upload folder permissions
ls -la /var/www/ptsc-dms/backend/uploads

# Fix permissions
sudo chown -R ptsc:ptsc /var/www/ptsc-dms/backend/uploads
sudo chmod 755 /var/www/ptsc-dms/backend/uploads
```

---

## 📚 Next Steps

1. ✅ Deploy application
2. ✅ Test all features
3. ⏳ Setup monitoring
4. ⏳ Configure backups
5. ⏳ Add custom domain
6. ⏳ Setup CI/CD pipeline

---

**Good luck with deployment! 🚀**
