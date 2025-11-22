# Quick Start Guide

Hướng dẫn nhanh để deploy PTSC DMS lên DigitalOcean trong 15 phút.

## 🚀 Cách nhanh nhất (App Platform)

### 1. Push lên GitHub (2 phút)

```bash
cd "Deploy Github"

git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/BAONGUYENCANH/ptsc-dms.git
git push -u origin main
```

### 2. Create App trên DigitalOcean (10 phút)

1. **Mở:** https://cloud.digitalocean.com/apps
2. **Click:** "Create App"
3. **Choose:** GitHub → `BAONGUYENCANH/ptsc-dms`
4. **Auto-detect:** DigitalOcean sẽ tự nhận diện cấu trúc
5. **Hoặc config manual:**

   **Backend:**
   - Name: `ptsc-backend`
   - Type: Web Service
   - Directory: `/backend`
   - Build: `pip install -r requirements.txt`
   - Run: `gunicorn app:app`
   - Port: 8080

   **Frontend:**
   - Name: `ptsc-frontend`
   - Type: Static Site
   - Directory: `/frontend`
   - Build: `npm install && npm run build`
   - Output: `dist`

6. **Choose Plan:** Basic ($5/month)
7. **Click:** "Create Resources"

### 3. Đợi Deploy (3 phút)

- Check logs
- Note down URLs khi xong

### 4. Test! (1 phút)

```
Frontend: https://ptsc-frontend-xxx.ondigitalocean.app
Backend: https://ptsc-backend-xxx.ondigitalocean.app/api/health
```

✅ **DONE!**

---

## 📋 Checklist

- [ ] Code đã push lên GitHub
- [ ] DigitalOcean App created
- [ ] Backend running (check /api/health)
- [ ] Frontend loads
- [ ] Can upload Excel file
- [ ] Dashboard displays data

---

## 🔧 Nếu có lỗi

### Build Failed

Check logs trong DigitalOcean dashboard → Click vào failed build

### Can't connect to backend

Update frontend environment variable:
```env
VITE_API_URL=https://ptsc-backend-xxx.ondigitalocean.app/api
```

Rebuild frontend trong DigitalOcean.

---

## 📚 Đọc thêm

- **Chi tiết đầy đủ:** `docs/DEPLOYMENT_GUIDE.md`
- **API docs:** `README.md`
- **Troubleshooting:** `docs/DEPLOYMENT_GUIDE.md#troubleshooting`

---

**That's it! Enjoy your deployed app! 🎉**
