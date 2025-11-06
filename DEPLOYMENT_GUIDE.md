# Deployment Guide - Financial Statements Verification Tool Web App

## 🚀 Quick Start: Deploy to Streamlit Cloud (FREE - 5 Minutes)

The easiest way to get your app online for free!

### Step 1: Prepare Your Files

Make sure you have these files:
- ✅ `app.py` - Main Streamlit app
- ✅ `comparatives_verification_tool.py` - Core logic
- ✅ `requirements.txt` - Dependencies
- ✅ `.streamlit/config.toml` - Configuration

### Step 2: Create GitHub Repository

```bash
# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Financial Verification Tool"

# Create repository on GitHub (via github.com)
# Then connect and push:
git remote add origin https://github.com/YOUR-USERNAME/financial-verification.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Streamlit Cloud

1. **Go to**: [share.streamlit.io](https://share.streamlit.io)
2. **Sign in** with your GitHub account
3. **Click** "New app"
4. **Select**:
   - Repository: `YOUR-USERNAME/financial-verification`
   - Branch: `main`
   - Main file path: `app.py`
5. **Click** "Deploy!"

**🎉 Done!** Your app will be live at:
```
https://your-app-name.streamlit.app
```

### Step 4: Test Your App

1. Open the URL
2. Upload sample financial statements
3. Click "Verify Comparatives"
4. Download the report

---

## 💡 Alternative Deployment Options

### Option 2: Heroku (Paid)

**Files needed**: `Procfile` and `runtime.txt` (already created)

```bash
# Install Heroku CLI first

# Login
heroku login

# Create app
heroku create your-app-name

# Deploy
git push heroku main

# Open
heroku open
```

**URL**: `https://your-app-name.herokuapp.com`

### Option 3: Docker (Any Platform)

**Dockerfile** (already created):

```bash
# Build
docker build -t fin-verification .

# Run locally
docker run -p 8501:8501 fin-verification

# Access at http://localhost:8501
```

### Option 4: Local Network

For internal company use:

```bash
# Install dependencies
pip install -r requirements.txt

# Run on network
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Access from other computers: `http://YOUR-IP:8501`

---

## 🔒 Security Tips

### Add Password Protection

Add to `app.py` at the top:

```python
import streamlit as st

def check_password():
    def password_entered():
        if st.session_state["password"] == "YourSecurePassword123":
            st.session_state["password_correct"] = True
    
    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", 
                     on_change=password_entered, key="password")
        return False
    
    return st.session_state["password_correct"]

if not check_password():
    st.stop()
```

### Limit File Sizes

Already configured in `.streamlit/config.toml`:
```toml
[server]
maxUploadSize = 200  # Max 200 MB
```

---

## 📊 Monitoring

### Streamlit Cloud
- View logs in dashboard
- Monitor app health
- See usage statistics

### Self-Hosted
```bash
# Check logs
streamlit run app.py --logger.level=info

# Docker logs
docker logs -f container-name
```

---

## 🔄 Updating Your App

### Streamlit Cloud
```bash
# Make changes to code
git add .
git commit -m "Updated feature"
git push

# App automatically redeploys!
```

### Docker
```bash
# Rebuild
docker build -t fin-verification .

# Stop old container
docker stop container-name

# Run new version
docker run -p 8501:8501 fin-verification
```

---

## 🎯 Recommended Deployment

**For Quick Demo**: → Streamlit Cloud (FREE, 5 min)  
**For Company Internal**: → Docker on company server  
**For Production**: → AWS/GCP with Docker  

---

## 📝 Complete File Structure

```
financial-verification-tool/
├── app.py                              # Streamlit web UI
├── comparatives_verification_tool.py   # Core logic
├── requirements.txt                    # Dependencies
├── .streamlit/
│   └── config.toml                    # Streamlit config
├── Dockerfile                         # Docker config
├── Procfile                           # Heroku config
├── runtime.txt                        # Python version
├── README.md                          # Project docs
├── USER_GUIDE.md                      # User manual
├── DEPLOYMENT_GUIDE.md                # This file
└── example_usage.py                   # Code examples
```

---

## 🐛 Troubleshooting

### "Module not found" error
```bash
# Ensure requirements.txt has all dependencies
pip install -r requirements.txt
```

### Port already in use
```bash
# Use different port
streamlit run app.py --server.port 8502
```

### Streamlit Cloud deployment fails
- Check all files are in GitHub repo
- Verify requirements.txt is correct
- Review build logs in dashboard

---

## 🎉 You're Ready!

**Next Steps**:
1. Deploy to Streamlit Cloud (takes 5 minutes)
2. Test with your financial statements
3. Share the URL with your team
4. Gather feedback and iterate

**Need help?** Check the troubleshooting section or Streamlit documentation.

---

**Made for Brane Group** 🚀
