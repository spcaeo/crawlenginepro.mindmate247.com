# 🚀 Deployment Guide - Git-Based Workflow

## Overview

We now have a proper Git-based deployment workflow:

```
Local Dev (Mac) → GitHub → Production Server
```

All code changes should be committed to Git, pushed to GitHub, and then pulled on the production server.

## Prerequisites

- ✅ GitHub repository: `https://github.com/spcaeo/crawlenginepro.mindmate247.com.git`
- ✅ SSH access to production server: `reku631@89.169.103.3`
- ✅ SSH key: `~/reku631_nebius`

---

## 📝 Step-by-Step Deployment Process

### 1. **Make Changes Locally** (Your Mac)

```bash
cd /Users/rakesh/Desktop/crawlenginepro.mindmate247.com

# Make your code changes
# Test locally to ensure everything works
```

### 2. **Commit to Git**

```bash
# Check what changed
git status

# Add files
git add .

# Commit with descriptive message
git commit -m "feat: Add new feature XYZ

- Detailed description of what changed
- Why the change was needed
- Any breaking changes or important notes"

# Push to GitHub
git push origin main
```

### 3. **Deploy to Production Server**

#### Option A: **Manual Deployment (Recommended for now)**

```bash
# SSH to production server
ssh -i ~/reku631_nebius reku631@89.169.103.3

# Navigate to project directory
cd ~/crawlenginepro

# FIRST TIME ONLY: Clone the repository
git clone https://github.com/spcaeo/crawlenginepro.mindmate247.com.git code_new
# Then backup old code and rename: mv code code_old && mv code_new code

# FOR UPDATES: Pull latest changes
cd ~/crawlenginepro/code
git pull origin main

# Restart services (if needed)
cd ~/crawlenginepro/code/deploy
./manage.sh restart
```

#### Option B: **Automated Deployment** (Future)

Run the deployment script from your local machine:

```bash
cd /Users/rakesh/Desktop/crawlenginepro.mindmate247.com/code/deploy
./deploy.sh --backup --restart
```

---

## 🗂️ Server Directory Structure

```
~/crawlenginepro/
├── code/                    # Your application code (Git-managed)
│   ├── Ingestion/
│   ├── Retrieval/
│   ├── shared/
│   ├── deploy/
│   └── .git/
├── milvus/                  # Database data (NEVER DELETE!)
│   ├── volumes/
│   └── docker-compose.yml
└── backups/                 # Old code backups (manual)
    ├── code_20251022_100000/
    └── code_20251022_110000/
```

### ⚠️ CRITICAL: Milvus Data

**NEVER touch the `milvus/` directory!** It contains all your vector database data.

- The `code/` directory can be deleted and re-cloned from Git
- The `milvus/` directory contains irreplaceable production data

---

## 🔧 Common Deployment Scenarios

### Scenario 1: **Small Code Fix**

```bash
# Local
git add .
git commit -m "fix: Correct typo in config"
git push origin main

# Production
ssh -i ~/reku631_nebius reku631@89.169.103.3
cd ~/crawlenginepro/code
git pull origin main
# No restart needed for config changes
```

### Scenario 2: **Major Feature Addition**

```bash
# Local
git add .
git commit -m "feat: Add new search algorithm"
git push origin main

# Production
ssh -i ~/reku631_nebius reku631@89.169.103.3
cd ~/crawlenginepro/code
git pull origin main
cd deploy
./manage.sh restart  # Restart services to load new code
```

### Scenario 3: **Emergency Rollback**

```bash
# Production
cd ~/crawlenginepro/code
git log --oneline -5  # See recent commits
git reset --hard <previous-commit-hash>  # Rollback to working version
cd deploy
./manage.sh restart
```

---

## 🛠️ Production Server Setup (First Time Only)

If you need to set up the production server from scratch:

```bash
# SSH to server
ssh -i ~/reku631_nebius reku631@89.169.103.3

# Navigate to project directory
cd ~/crawlenginepro

# Backup old messy code
mv code code_old_$(date +%Y%m%d_%H%M%S)

# Clone fresh code from GitHub
git clone https://github.com/spcaeo/crawlenginepro.mindmate247.com.git code

# Set up environment
cd code/shared
cp .env.dev .env.prod  # Create production environment file
nano .env.prod  # Edit with production settings

# Set up Python environment (if needed)
cd ~/crawlenginepro
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # If you have one

# Start services
cd code/deploy
./manage.sh start

# Check status
./manage.sh status
```

---

## 📊 Service Management

### Start All Services
```bash
cd ~/crawlenginepro/code/deploy
./manage.sh start
```

### Stop All Services
```bash
./manage.sh stop
```

### Restart All Services
```bash
./manage.sh restart
```

### Check Status
```bash
./manage.sh status
```

### View Logs
```bash
./manage.sh logs
```

---

## 🔐 Environment Configuration

Production uses environment-specific config files:

- **Development**: `code/shared/.env.dev`
- **Production**: `code/shared/.env.prod`

**Important**: `.env.prod` is NOT in Git (for security). You must manually create/update it on the server.

### Required Environment Variables:

```bash
# code/shared/.env.prod
PIPELINE_ENV=prod
ENVIRONMENT=production

# Milvus
MILVUS_HOST_PRODUCTION=localhost
MILVUS_PORT_PRODUCTION=19530

# LLM Gateway
LLM_GATEWAY_API_KEY=your_production_key_here

# Service Ports (Production)
INGESTION_API_PORT=8070
# ... (other services)
```

---

## 📝 Git Best Practices

### Commit Message Format:

```
<type>: <short description>

<detailed description>
<why this change was made>
<any breaking changes>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `perf`: Performance improvements
- `test`: Adding tests
- `chore`: Maintenance tasks

### Example:

```bash
git commit -m "feat: Add context-aware metadata extraction

- Metadata fields now adapt to document type
- Religious content uses deity/scripture fields
- Business content uses industry/payment fields
- Fixes issue where all documents used business terminology

Breaking change: Metadata schema updated, requires re-ingestion"
```

---

## 🚨 Troubleshooting

### Problem: Git pull fails with conflicts

```bash
# Option 1: Stash local changes
git stash
git pull origin main
git stash pop

# Option 2: Hard reset to remote (⚠️ loses local changes)
git fetch origin
git reset --hard origin/main
```

### Problem: Services won't start after deployment

```bash
# Check logs
cd ~/crawlenginepro/code/deploy
./manage.sh logs

# Verify environment
cd ~/crawlenginepro/code/shared
cat .env.prod  # Make sure it exists and has correct values

# Check Python environment
which python3
python3 --version

# Restart manually
./manage.sh restart
```

### Problem: Milvus connection fails

```bash
# Check if Milvus is running
cd ~/crawlenginepro/milvus
docker-compose ps

# If not running
docker-compose up -d

# Check Milvus logs
docker-compose logs -f milvus-standalone
```

---

## 📚 Quick Reference

### Local Development
```bash
# Make changes → Test → Commit → Push
git add .
git commit -m "your message"
git push origin main
```

### Production Deployment
```bash
# SSH → Pull → Restart
ssh -i ~/reku631_nebius reku631@89.169.103.3
cd ~/crawlenginepro/code
git pull origin main
cd deploy && ./manage.sh restart
```

### Check Everything is Working
```bash
# On server
cd ~/crawlenginepro/code/deploy
./manage.sh status
./manage.sh logs | tail -50
```

---

## 🎯 Next Steps

1. ✅ Code is in GitHub
2. ⏳ Clean up production server code directory
3. ⏳ Pull latest code on production
4. ⏳ Test everything works
5. ⏳ Document any production-specific settings

**Remember**: Always test locally first, commit to Git, then deploy to production!
