# PTSC Document Management System - DigitalOcean Deployment

Full-stack web application for managing PTSC documents with Python backend and React frontend.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│  React Frontend (Vite + TypeScript)         │
│  - Dashboard with charts                    │
│  - Excel import UI                          │
│  - Document table with filters              │
└─────────────────┬───────────────────────────┘
                  │ HTTP API
┌─────────────────▼───────────────────────────┐
│  Flask Backend (Python)                     │
│  - Excel file processing                    │
│  - SQLite database                          │
│  - REST API endpoints                       │
└─────────────────────────────────────────────┘
```

## 📁 Project Structure

```
Deploy Github/
├── frontend/              # React + Vite application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── utils/        # Utilities (mdi-parser, etc.)
│   │   ├── types/        # TypeScript types
│   │   └── store/        # State management
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── backend/              # Flask API server
│   ├── scripts/          # Python scripts
│   │   ├── export_db_to_json_v2.py
│   │   ├── excel_importer.py
│   │   └── ...
│   ├── app.py           # Main Flask application
│   ├── requirements.txt # Python dependencies
│   └── uploads/         # Temporary file uploads
│
├── docs/                # Documentation
├── .gitignore
└── README.md
```

## 🚀 Local Development

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- pip

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
# Backend runs on http://localhost:5000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
# Frontend runs on http://localhost:5173
```

### Access Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:5000/api/health

## 🌐 DigitalOcean Deployment

### Option 1: App Platform (Recommended - Easy)

#### Step 1: Push to GitHub

```bash
# Initialize git in Deploy Github folder
cd "Deploy Github"
git init
git add .
git commit -m "Initial commit: PTSC DMS full-stack"

# Add remote
git remote add origin https://github.com/BAONGUYENCANH/ptsc-dms.git

# Push
git push -u origin main
```

#### Step 2: Create App on DigitalOcean

1. Go to: https://cloud.digitalocean.com/apps
2. Click **"Create App"**
3. Choose **"GitHub"** as source
4. Select repository: `BAONGUYENCANH/ptsc-dms`
5. Configure components:

**Backend Component:**
```yaml
Name: ptsc-backend
Type: Web Service
Source Directory: /backend
Build Command: pip install -r requirements.txt
Run Command: gunicorn app:app
Port: 5000
Environment Variables:
  - FLASK_ENV=production
  - PORT=5000
```

**Frontend Component:**
```yaml
Name: ptsc-frontend
Type: Static Site
Source Directory: /frontend
Build Command: npm install && npm run build
Output Directory: /dist
```

6. Choose plan:
   - **Basic** plan: $5-12/month
   - or use GitHub Student Pack credit!

7. Click **"Create Resources"**

#### Step 3: Configure Environment Variables

In DigitalOcean App Platform settings:

```env
# Backend
FLASK_ENV=production
DATABASE_URL=sqlite:///project_data.db

# Frontend (build time)
VITE_API_URL=https://ptsc-backend-xxx.ondigitalocean.app
```

#### Step 4: Update Frontend API Endpoint

Create `frontend/.env.production`:

```env
VITE_API_URL=https://YOUR_BACKEND_URL.ondigitalocean.app/api
```

Update `frontend/src/utils/api.ts` (create if not exists):

```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const api = {
  uploadExcel: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    
    return response.json();
  },
  
  getDocuments: async () => {
    const response = await fetch(`${API_URL}/documents`);
    return response.json();
  },
  
  getStats: async () => {
    const response = await fetch(`${API_URL}/stats`);
    return response.json();
  },
};
```

### Option 2: Droplet (Manual - More Control)

#### Step 1: Create Droplet

1. Create Ubuntu 22.04 droplet ($6/month)
2. SSH into droplet:
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

#### Step 2: Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python
apt install python3 python3-pip python3-venv -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install nodejs -y

# Install Nginx
apt install nginx -y

# Install Certbot (SSL)
apt install certbot python3-certbot-nginx -y
```

#### Step 3: Clone Repository

```bash
cd /var/www
git clone https://github.com/BAONGUYENCANH/ptsc-dms.git
cd ptsc-dms
```

#### Step 4: Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service
nano /etc/systemd/system/ptsc-backend.service
```

Add content:

```ini
[Unit]
Description=PTSC Backend API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/ptsc-dms/backend
Environment="PATH=/var/www/ptsc-dms/backend/venv/bin"
ExecStart=/var/www/ptsc-dms/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
systemctl enable ptsc-backend
systemctl start ptsc-backend
systemctl status ptsc-backend
```

#### Step 5: Setup Frontend

```bash
cd /var/www/ptsc-dms/frontend

# Install dependencies
npm install

# Build
npm run build

# Copy to Nginx
cp -r dist/* /var/www/html/
```

#### Step 6: Configure Nginx

```bash
nano /etc/nginx/sites-available/ptsc-dms
```

Add content:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Or use IP

    # Frontend
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable site:

```bash
ln -s /etc/nginx/sites-available/ptsc-dms /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### Step 7: Setup SSL (Optional but Recommended)

```bash
certbot --nginx -d your-domain.com
```

### Access Your App

- **App Platform**: `https://ptsc-frontend-xxx.ondigitalocean.app`
- **Droplet**: `http://YOUR_DROPLET_IP` or `https://your-domain.com`

## 🔧 Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_PATH=project_data.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
```

### Frontend Environment Variables

Create `frontend/.env.production`:

```env
VITE_API_URL=https://your-backend-url/api
```

## 📡 API Endpoints

### GET /api/health
Health check

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-22T08:00:00",
  "database": true
}
```

### GET /api/documents
Get all documents

**Response:**
```json
{
  "success": true,
  "data": {
    "metadata": { ... },
    "documents": [ ... ]
  }
}
```

### POST /api/upload
Upload Excel file

**Request:** multipart/form-data with `file` field

**Response:**
```json
{
  "success": true,
  "message": "Imported 500 documents",
  "data": { "count": 500 }
}
```

### GET /api/stats
Get database statistics

**Response:**
```json
{
  "success": true,
  "stats": {
    "total": 500,
    "overdue": 45,
    "disciplines": [ ... ],
    "statuses": [ ... ]
  }
}
```

### GET /api/export
Export database to JSON

**Response:** JSON file download

## 🧪 Testing

### Backend Tests

```bash
cd backend
python -m pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 📊 Monitoring

### Logs

**Backend (systemd):**
```bash
journalctl -u ptsc-backend -f
```

**Nginx:**
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### DigitalOcean Metrics

View metrics in App Platform dashboard:
- Request count
- Response time
- Error rate
- Memory/CPU usage

## 🔄 Updates

### Deploy Updates (App Platform)

```bash
git add .
git commit -m "Update: feature description"
git push origin main
# DigitalOcean auto-deploys
```

### Deploy Updates (Droplet)

```bash
# SSH to droplet
cd /var/www/ptsc-dms

# Pull updates
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
systemctl restart ptsc-backend

# Update frontend
cd ../frontend
npm install
npm run build
cp -r dist/* /var/www/html/

# Restart Nginx
systemctl restart nginx
```

## 💰 Costs (with GitHub Student Pack)

- **App Platform**: $0 (free credits)
- **Droplet**: $6/month (Basic)
- **Domain**: Optional (~$12/year)

## 🐛 Troubleshooting

### Backend not starting

```bash
# Check logs
journalctl -u ptsc-backend -n 50

# Check if port is in use
netstat -tlnp | grep 5000

# Restart service
systemctl restart ptsc-backend
```

### Frontend not loading

```bash
# Check Nginx config
nginx -t

# Check build output
ls -la /var/www/html/

# Rebuild frontend
cd /var/www/ptsc-dms/frontend
npm run build
```

### Database locked error

```bash
# Stop backend
systemctl stop ptsc-backend

# Check for lock
lsof | grep project_data.db

# Restart
systemctl start ptsc-backend
```

## 📚 Additional Resources

- [DigitalOcean App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [GitHub Student Pack](https://education.github.com/pack)
- [Flask Deployment](https://flask.palletsprojects.com/en/3.0.x/deploying/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)

## 📝 License

Proprietary - PTSC Internal Use Only

## 👥 Support

For issues or questions, contact the development team.

---

**Built with ❤️ for PTSC**
