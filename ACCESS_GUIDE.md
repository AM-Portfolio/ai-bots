# 🚀 Quick Access Guide - AI Development Agent

## 📍 How to Access Your Application

### 🔧 Backend API (FastAPI)

**Port:** 5000  
**Status:** ✅ Running

**Access URLs:**
- **In Replit:** Click the "Webview" button or use the auto-generated URL
- **Direct:** `https://[your-replit-url].repl.co`

**What you can do:**
- Access interactive API documentation: `/docs`
- View API health: `/health`
- Check metrics: `/metrics`
- Use all REST endpoints: `/api/*`

**Example:**
```bash
# Check API health
curl https://[your-replit-url].repl.co/health

# View API docs
https://[your-replit-url].repl.co/docs
```

---

### 🎨 Testing UI (Streamlit)

**Port:** 8501  
**Status:** ✅ Running

**Access URLs:**
- **In Replit:** The UI runs on port 8501
- **How to access:**
  1. Look for the workflow output showing: `URL: http://0.0.0.0:8501`
  2. Or use port forwarding to access at: `https://[your-replit-url].repl.co:8501`

**What you can do:**
- Test all 8 features individually through UI
- Run complete analysis workflows
- View real-time results
- No code required - just use the web interface!

**Features Available:**
1. 🧠 LLM Testing
2. 🐙 GitHub Integration
3. 📋 Jira Integration
4. 📚 Confluence Integration
5. 📊 Grafana Integration
6. 🔄 Context Resolver
7. 🔍 Code Analysis
8. ✅ Test Generation
9. 🚀 Full Analysis Workflow

---

## ⚡ Quick Start

### Step 1: Verify Both Are Running

Check the workflows in Replit:
- ✅ **Server** (Port 5000) - Backend API
- ✅ **UI** (Port 8501) - Testing Interface

### Step 2: Access the API

Click the Webview button in Replit to see:
```json
{
  "service": "AI Dev Agent",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "analyze": "/api/analyze",
    "webhook": "/api/webhook"
  }
}
```

### Step 3: Access the UI

1. Find the UI workflow output
2. Note the URL: `http://0.0.0.0:8501`
3. Access via port forwarding or Replit's port viewer

### Step 4: Start Testing!

Open the UI and:
1. Check the API health indicator (should be green ✅)
2. Choose a tab to test a specific feature
3. Enter required parameters
4. Click the test button
5. View results instantly!

---

## 🔧 If Something Isn't Working

### Backend Not Accessible
```bash
# Restart the Server workflow
python main.py
```

### UI Not Loading
```bash
# Restart the UI workflow
cd ui && streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Both Workflows Stopped
- Go to the Replit workflows panel
- Click the restart button for each workflow

---

## 📊 API Documentation

**Interactive Docs:** `https://[your-url].repl.co/docs`

### Main Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |
| `/api/analyze` | POST | Analyze issue (complete workflow) |
| `/api/webhook/{source}` | POST | Receive webhooks |

### Test Endpoints (8 Individual Features)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/test/llm` | POST | Test LLM provider |
| `/api/test/github` | POST | Test GitHub |
| `/api/test/jira` | POST | Test Jira |
| `/api/test/confluence` | POST | Test Confluence |
| `/api/test/grafana` | POST | Test Grafana |
| `/api/test/context-resolver` | POST | Test context resolver |
| `/api/test/code-analysis` | POST | Test code analysis |
| `/api/test/generate-tests` | POST | Test generation |

---

## 🎯 Common Use Cases

### Test LLM Provider

**Via UI:**
1. Go to "LLM Testing" tab
2. Enter prompt
3. Select provider
4. Click "Test LLM"

**Via API:**
```bash
curl -X POST "https://[your-url].repl.co/api/test/llm?prompt=Hello&provider=together"
```

### Analyze a GitHub Issue

**Via UI:**
1. Go to "Full Analysis Workflow" tab
2. Enter issue ID and repository
3. Enable options (create PR, publish docs)
4. Click "Run Full Analysis"

**Via API:**
```bash
curl -X POST "https://[your-url].repl.co/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id": "123",
    "source": "github",
    "repository": "owner/repo",
    "create_pr": true,
    "publish_docs": false
  }'
```

---

## 🚀 Deployment (Publishing)

To make your app publicly accessible with a persistent URL:

1. **Configure deployment settings** (deployment config is already set up)
2. Click the **"Deploy"** or **"Publish"** button in Replit
3. Your app will be deployed to production
4. You'll get a public URL that's always available

**Deployment Mode:** Autoscale (stateless web app)
- Automatically scales based on traffic
- Runs on demand
- Cost-effective for APIs

---

## 📚 More Documentation

- `README.md` - Project overview
- `CONFIGURATION.md` - Setup all integrations
- `API_ENDPOINTS.md` - Complete API reference
- `UI_TESTING_GUIDE.md` - Detailed UI testing guide
- `LLM_PROVIDER_GUIDE.md` - LLM setup guide

---

## 🎉 You're All Set!

Both the **Backend API** and **Testing UI** are running and ready to use!

**Backend:** Port 5000 (FastAPI)  
**UI:** Port 8501 (Streamlit)  

Access them through Replit's interface and start testing your AI Development Agent! 🤖
