# ⚡ Quick Test Steps - Together AI

## 🚀 **5-Minute Testing Guide**

### **Step 1: Open Your App** (30 seconds)
- Your app is already running at **port 5000**
- It should show in the Replit webview automatically
- You'll see the **"AI Dev Agent"** sidebar on the left

### **Step 2: Test Together AI** (2 minutes)

1. **Click "LLM Testing"** in the sidebar
2. **Verify settings:**
   - Provider: `Together AI (Llama-3.3-70B)` ✅
   - Show Backend Details: `☐ Unchecked` (for clean UI)
3. **Send the default message:**
   - Default prompt: `"What are some best practices for writing clean Python code?"`
   - Click **"Send"** button
4. **Wait 2-5 seconds** - you'll see:
   - ⏳ "Thinking..." spinner
   - 🤖 AI response in blue bubble
   - ✅ Response time and status

**✅ Success Criteria:** You get a coherent response about Python best practices

### **Step 3: Test Backend Details** (1 minute)

1. **Check "Show Backend Details"** checkbox
2. **Send another message:** `"Explain async/await in JavaScript"`
3. **You should see:**
   - 🔍 Step 1: Provider Selection (expandable)
   - 📤 Step 2: Sending API Request (expandable)
   - 📥 Step 3: API Response Received (expandable)
4. **Click the arrows** to expand/collapse steps

**✅ Success Criteria:** Backend details show technical information and response metrics

### **Step 4: Test Other Panels** (1.5 minutes)

**GitHub Panel:**
- Click **"GitHub"** → Enter `octocat/Hello-World` → Click **"Test"**
- Should show repository info or "GitHub token not configured"

**Integrations Panel:**
- Click **"Integrations"** → See Jira, Confluence, Grafana cards
- Optional: Click test buttons to see status

**Doc Orchestrator:**
- Click **"Doc Orchestrator"** → See workflow interface
- Note: Requires full configuration to run

**Full Analysis:**
- Click **"Full Analysis"** → See analysis form
- Note: Requires GitHub repository access

### **Step 5: Verify API Health** (30 seconds)

Open Replit Shell and run:
```bash
curl http://localhost:8000/health
```

**Expected Output:**
```json
{"status":"healthy"}
```

---

## 🎯 **Testing Summary**

| Test | What to Check | Expected Result |
|------|---------------|-----------------|
| **LLM Chat** | Send message with Together AI | AI responds in 2-10s with coherent text |
| **Backend Details** | Toggle on and send message | Shows 3 collapsible steps with metrics |
| **UI Navigation** | Click all 5 sidebar items | Each panel loads without errors |
| **API Health** | `curl localhost:8000/health` | Returns `{"status":"healthy"}` |

---

## ✅ **Quick Validation Checklist**

- [ ] App loads in Replit webview (port 5000)
- [ ] Sidebar shows 5 navigation items
- [ ] LLM Testing panel responds to prompts
- [ ] Together AI returns answers (2-10s)
- [ ] Backend Details toggle works
- [ ] All 5 panels are accessible
- [ ] No console errors in browser
- [ ] Backend health check passes

---

## 🐛 **Quick Troubleshooting**

**Problem:** No response from AI
- **Check:** Backend logs for "Together AI credentials not configured"
- **Fix:** Verify `TOGETHER_API_KEY` is set in Replit Secrets

**Problem:** "Connection failed"
- **Check:** `curl http://localhost:8000/health`
- **Fix:** Restart the workflow in Replit

**Problem:** UI not loading
- **Check:** Console for errors (F12 → Console tab)
- **Fix:** Clear browser cache and refresh

---

## 📊 **Performance Benchmarks**

| Metric | Expected Value | Your Result |
|--------|---------------|-------------|
| Response Time | 2-10 seconds | _____ |
| UI Load Time | < 2 seconds | _____ |
| API Health Check | < 100ms | _____ |
| Backend Status | Running ✅ | _____ |

---

## 🚀 **Next: Deploy to Production**

Once testing passes:
1. Click **"Publish"** button in Replit
2. Get your live URL: `https://your-app.replit.app`
3. Share with users! 🎉

---

## 📝 **Test Results Log**

**Test Date:** _____________

**Together AI Test:**
- [ ] Default prompt responded successfully
- [ ] Response time: _____ seconds
- [ ] Backend details showed correctly
- [ ] Multiple messages work sequentially

**UI Test:**
- [ ] All panels accessible
- [ ] Navigation smooth
- [ ] No console errors
- [ ] Mobile-responsive

**API Test:**
- [ ] Health endpoint: `{"status":"healthy"}`
- [ ] Service info: Correct JSON
- [ ] LLM endpoint: Working

**Overall Status:** ✅ PASSED / ❌ FAILED

**Notes:**
_________________________________
_________________________________
_________________________________

---

For detailed testing, see **TOGETHER_AI_TESTING_GUIDE.md**
