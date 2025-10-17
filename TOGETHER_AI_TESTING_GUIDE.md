# Together AI Testing Guide

## 🚀 Complete Testing Steps for AI Dev Agent

This guide provides step-by-step instructions to test the Together AI integration with your deployed AI Dev Agent application.

---

## ✅ **Prerequisites**

Before testing, ensure you have:

1. **Together API Key configured** (already set as `TOGETHER_API_KEY` secret in Replit)
2. **Application running** on Replit (both frontend and backend)
3. **Access to the web interface** via the Replit webview

---

## 📋 **Testing Checklist**

### **Phase 1: Basic LLM Testing (Core Functionality)**

#### Test 1: Simple Query with Together AI
1. **Navigate to LLM Testing Panel**
   - Open your Replit app (port 5000 shows in webview)
   - Click on **"LLM Testing"** in the left sidebar
   - Verify you see the ChatGPT-like interface

2. **Configure Settings**
   - Provider: Select **"Together AI (Llama-3.3-70B)"**
   - Show Backend Details: **Uncheck** for clean UI

3. **Send Test Message**
   - Use the default prompt: `"What are some best practices for writing clean Python code?"`
   - Click **"Send"** button (or press Enter)
   
4. **Verify Response**
   - ✅ Should show "Thinking..." spinner
   - ✅ AI response appears in blue bubble
   - ✅ Response time displayed (typically 2-5 seconds)
   - ✅ Provider shown as "together"

#### Test 2: Backend Details Mode
1. **Enable Backend Visibility**
   - Check **"Show Backend Details"** checkbox
   - Send another message

2. **Verify Detailed Output**
   - ✅ Should see collapsible sections:
     - 🔍 Step 1: Provider Selection
     - 📤 Step 2: Sending API Request
     - 📥 Step 3: API Response Received
   - ✅ Each section shows technical details
   - ✅ Click arrows to expand/collapse

#### Test 3: Different Query Types
Test various prompts to verify Together AI capabilities:

```
1. Code Generation:
"Write a Python function to calculate fibonacci numbers"

2. Debugging Help:
"Explain what causes a NullPointerException in Java"

3. Architecture Advice:
"What are the pros and cons of microservices vs monolithic architecture?"

4. Creative Writing:
"Write a haiku about artificial intelligence"
```

**Expected Results:**
- ✅ All responses should be coherent and relevant
- ✅ Response times: 2-10 seconds
- ✅ No errors in backend logs
- ✅ Chat history preserved in UI

---

### **Phase 2: GitHub Integration Testing**

#### Test 4: GitHub Repository Access
1. **Navigate to GitHub Panel**
   - Click **"GitHub"** in sidebar
   
2. **Test Public Repository**
   - Repository: `octocat/Hello-World`
   - Click **"Test GitHub Integration"**

3. **Verify Results**
   - ✅ Success message with green checkmark
   - ✅ Repository name displayed
   - ✅ Default branch shown (master/main)
   - ✅ Recent issues listed (if any)

**Note:** GitHub integration may require the GitHub token to be configured. If you see "GitHub token not configured", this is expected and not a failure.

---

### **Phase 3: Integration Testing**

#### Test 5: Multiple Integrations
1. **Navigate to Integrations Panel**
   - Click **"Integrations"** in sidebar

2. **Test Each Service** (if configured):
   - **Jira:** Click "Test Integration" → Should show projects or config message
   - **Confluence:** Click "Test Integration" → Should show spaces or config message
   - **Grafana:** Click "Test Integration" → Should show datasources or config message

**Expected Results:**
- ✅ Each card shows test button
- ✅ Loading spinner during test
- ✅ Success/failure status with appropriate message
- ✅ "Not configured" messages are normal if credentials not set

---

### **Phase 4: Documentation Orchestrator**

#### Test 6: AI-Powered Documentation Workflow
1. **Navigate to Doc Orchestrator**
   - Click **"Doc Orchestrator"** in sidebar

2. **Configure Test**
   - Prompt: `"Document the authentication module in the project"`
   - Repository: `owner/repo` (use your GitHub repo)
   - Confluence Space: (optional)
   - Jira Project: (optional)

3. **Run Orchestration**
   - Click **"Start Documentation Workflow"**

4. **Monitor Progress**
   - ✅ Step-by-step progress indicators
   - ✅ Each step shows status (pending → running → complete)
   - ✅ Success/error messages for each phase

**Note:** Full orchestration requires GitHub, Confluence, and Jira credentials.

---

### **Phase 5: Full Issue Analysis**

#### Test 7: Complete AI Analysis Pipeline
1. **Navigate to Full Analysis**
   - Click **"Full Analysis"** in sidebar

2. **Configure Analysis**
   - Source: **GitHub**
   - Issue ID: `123` (or any valid issue number)
   - Repository: `owner/repo`

3. **Run Analysis**
   - Click **"Analyze Issue"**

4. **Verify Results**
   - ✅ Analysis runs with loading spinner
   - ✅ Success/error message displayed
   - ✅ JSON results shown (if successful)

---

### **Phase 6: API Testing (Advanced)**

#### Test 8: Direct API Endpoints

Use `curl` or Postman to test backend directly:

**Health Check:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

**Service Info:**
```bash
curl http://localhost:8000/
# Expected: JSON with service name, version, endpoints
```

**LLM Test (Together AI):**
```bash
curl -X POST "http://localhost:8000/api/test/llm?prompt=Hello&provider=together"
# Expected: {"success": true, "response": "...", "provider_used": "together"}
```

**GitHub Test:**
```bash
curl -X POST "http://localhost:8000/api/test/github?repository=octocat/Hello-World"
# Expected: {"success": true, "repository": "...", "issues": [...]}
```

---

### **Phase 7: Performance & Reliability**

#### Test 9: Multiple Concurrent Requests
1. **Open Multiple Browser Tabs**
   - Open 3 tabs with your app
   - Send different messages simultaneously

2. **Verify Behavior**
   - ✅ All requests handled independently
   - ✅ No request blocking others
   - ✅ Responses arrive in order sent

#### Test 10: Fallback Testing (if Azure OpenAI configured)
1. **Switch Provider**
   - Select **"Azure OpenAI (GPT-4)"** in dropdown
   - Send test message

2. **Verify Fallback**
   - ✅ If Azure works, response comes from Azure
   - ✅ If Azure fails, should fallback to Together AI
   - ✅ Backend Details shows which provider was used

---

## 🔍 **Troubleshooting**

### Common Issues & Solutions

**Issue 1: "API Error" or No Response**
- **Cause:** Together API key not configured
- **Solution:** Verify `TOGETHER_API_KEY` is set in Replit Secrets
- **Check:** Look at backend logs for "Together AI credentials not configured"

**Issue 2: "Connection Failed"**
- **Cause:** Backend not running on port 8000
- **Solution:** Restart the workflow in Replit
- **Check:** Visit http://localhost:8000/health

**Issue 3: GitHub/Jira/Confluence Errors**
- **Cause:** Integration credentials not configured
- **Solution:** This is expected - configure in `.env` or Replit Secrets
- **Note:** These are optional for LLM testing

**Issue 4: Slow Responses**
- **Cause:** Large prompts or complex queries
- **Solution:** Normal - Together AI may take 5-15s for complex requests
- **Check:** Backend Details shows actual response time

---

## 📊 **Success Criteria**

Your deployment is successful if:

✅ **Core Features:**
- [ ] LLM Testing panel loads without errors
- [ ] Together AI responds to prompts (2-10s response time)
- [ ] Message bubbles display correctly (user in gray, AI in blue)
- [ ] "Show Backend Details" toggle works
- [ ] Multiple messages can be sent in sequence
- [ ] Chat history persists during session

✅ **Integration Features:**
- [ ] All 5 panels are accessible via sidebar
- [ ] GitHub panel shows UI (integration optional)
- [ ] Integrations panel shows all 3 cards
- [ ] Doc Orchestrator shows workflow UI
- [ ] Full Analysis shows form

✅ **Backend Health:**
- [ ] `/health` returns `{"status":"healthy"}`
- [ ] `/` returns service info JSON
- [ ] `/api/test/llm` returns Together AI responses
- [ ] No errors in backend logs

✅ **UI/UX:**
- [ ] Sidebar navigation works smoothly
- [ ] Headers update based on active panel
- [ ] Loading spinners show during requests
- [ ] Error messages display when appropriate
- [ ] Responsive design works on different screens

---

## 🚀 **Next Steps After Testing**

Once testing is complete:

1. **Deploy to Production**
   - Click "Publish" in Replit to get live URL
   - Your app will be available at `https://your-app.replit.app`

2. **Configure Optional Integrations**
   - Add GitHub token for full repository access
   - Add Jira credentials for ticket management
   - Add Confluence for documentation publishing
   - Add Grafana for metrics/alerting

3. **Monitor Performance**
   - Check Prometheus metrics at `/metrics`
   - Review logs in Replit console
   - Monitor API response times

4. **Customize & Extend**
   - Add custom prompts to LLM testing
   - Extend API with new endpoints
   - Add more UI panels as needed

---

## 📚 **Additional Resources**

- **API Documentation:** Visit `http://localhost:8000/docs` for interactive Swagger docs
- **Configuration Guide:** See `CONFIGURATION.md` for detailed setup
- **Architecture Overview:** See `replit.md` for project structure
- **LLM Provider Guide:** See `LLM_PROVIDER_GUIDE.md` for provider details

---

## ✨ **Quick Test Commands**

Run these in Replit Shell for quick verification:

```bash
# Check if backend is running
curl http://localhost:8000/health

# Test Together AI directly
curl -X POST "http://localhost:8000/api/test/llm?prompt=Hello%20World&provider=together"

# Check service status
curl http://localhost:8000/

# View build output
ls -lh frontend/dist/

# Check logs
tail -100 /tmp/logs/AI_Dev_Agent_*.log
```

---

## 🎉 **Congratulations!**

If all tests pass, your AI Dev Agent is fully operational with:
- ✅ React + TypeScript frontend
- ✅ FastAPI backend with Together AI
- ✅ Multi-provider LLM support
- ✅ Beautiful ChatGPT-like UI
- ✅ Integration capabilities for GitHub, Jira, Confluence, Grafana

**Happy Testing!** 🚀
