# 🎤 Voice Assistant Troubleshooting Guide

## Current Issue
The Voice Assistant panel is not capturing voice input or sending it to the backend for processing.

## Quick Diagnosis

### ✅ What's Working
- ✅ Backend API is healthy
- ✅ Voice session creation endpoint works (`POST /api/voice/session`)
- ✅ Azure Speech services are configured
- ✅ Frontend is loaded

### ❌ What's NOT Working
- ❌ No voice processing requests reaching backend (`POST /api/voice/process`)
- ❌ Microphone not capturing audio
- ❌ Voice not being sent for transcription

## How to Use the Voice Assistant

### **Step 1: Navigate to Voice Assistant**
1. Open your app at `http://localhost:5000`
2. **Click on "🎤 Voice Assistant"** in the left sidebar (NOT "LLM Testing")

### **Step 2: Allow Microphone Access**
When you click on the Voice Assistant panel:
1. Browser will show a popup: **"Allow microphone access?"**
2. **Click "Allow"** to grant permission
3. You should see the animated voice visualization appear

### **Step 3: Start Speaking**
1. The AI will automatically greet you with voice
2. Wait for the greeting to finish
3. It will automatically start listening (you'll see "Listening..." and a blue pulsing circle)
4. **Speak clearly** into your microphone
5. After you stop speaking (1.5 second pause), it will:
   - Show "Processing..." (purple circle)
   - Send your audio to the backend
   - Get AI response
   - Show "Speaking..." (indigo circle)
   - Play back the voice response

## Common Issues & Solutions

### Issue 1: Microphone Permission Denied
**Symptoms:** Error message "Microphone access denied"

**Solution:**
1. Check browser permissions:
   - Chrome: Click lock icon in address bar → Site settings → Microphone → Allow
   - Firefox: Click lock icon → Clear permissions → Reload page
   - Safari: Safari menu → Settings → Websites → Microphone → Allow

2. Check system microphone:
   - Make sure your microphone is plugged in
   - Test in system settings to verify it's working
   - Close other apps using the microphone (Zoom, Teams, etc.)

### Issue 2: No Audio Being Captured
**Symptoms:** Button says "Voice Active" but no audio is being recorded

**Solution:**
1. Open browser DevTools (F12 or Ctrl+Shift+I)
2. Go to **Console** tab
3. Look for errors like:
   ```
   NotAllowedError: Permission denied
   NotFoundError: Requested device not found
   ```
4. Grant microphone permission or select the correct device

### Issue 3: Voice Not Responding
**Symptoms:** You speak but nothing happens

**Solution:**
1. Check backend logs for errors:
   - Look for `/api/voice/process` requests
   - Check for STT (Speech-to-Text) errors
   
2. Verify Azure Speech service is configured:
   ```bash
   # Check .env file has:
   AZURE_SPEECH_KEY=***
   AZURE_SPEECH_REGION=eastus2
   VOICE_STT_PROVIDER=azure
   ```

3. Try speaking louder and clearer
4. Wait for the 1.5 second pause detection

### Issue 4: Browser Compatibility
**Symptoms:** Voice features not working at all

**Supported Browsers:**
- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ⚠️ Safari (may have issues with WebM format)

**Solution for Safari:**
- Use Chrome or Firefox instead
- Or modify frontend to use different audio format

## Testing the Voice Assistant

### Manual Test (Without UI)

Test the backend API directly:

```bash
# 1. Create a session
curl -X POST http://localhost:5000/api/voice/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user"}'

# Expected response:
{
  "session_id": "...",
  "created_at": "...",
  "turn_count": 0,
  "status": "active"
}

# 2. Test voice processing (you'd need actual audio base64)
# This requires recording audio and converting to base64
```

### Frontend Console Test

Open browser console and check for these logs when using Voice Assistant:

```javascript
// Expected logs:
"✅ Voice session initialized: [session-id]"
"🎤 Started recording..."
"📤 Sending [size] bytes to backend..."
"📝 Transcript: [your speech]"
"🎯 Intent: [detected intent]"
"🔊 Playing AI response..."
```

## Debug Mode

### Enable Verbose Logging in Browser

1. Open DevTools Console (F12)
2. Look for these Voice Assistant logs:
   - Session creation
   - Recording start/stop
   - Audio processing
   - API requests

### Expected Backend Log Flow

When voice works correctly, you should see:

```
🎤 Processing voice for session: [id]
🎧 Transcribing audio (format: webm)...
📝 Transcript: "[your speech]"
🔍 Classifying intent for: "[your speech]"
✅ Classified as 'general' (confidence: 0.95)
🎤 Formatting response for voice (length: [chars])
✅ Voice response ready (final length: [chars])
🔊 Synthesizing speech (length: [chars])
✅ API POST /api/voice/process status=200
```

### If Backend Logs Show NO Voice Requests

This means the frontend is NOT sending audio. Check:

1. **Microphone permission** - Browser must have access
2. **JavaScript errors** - Check browser console for errors
3. **Network errors** - Check Network tab in DevTools for failed requests
4. **Wrong panel** - Make sure you're on "Voice Assistant" not "LLM Testing"

## Quick Fix Steps

1. **Hard refresh the browser:** Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. **Clear browser cache:** Settings → Privacy → Clear browsing data
3. **Grant microphone permission:** Click lock icon → Site settings → Microphone → Allow
4. **Check you're on Voice Assistant panel:** Left sidebar → 🎤 Voice Assistant
5. **Wait for greeting:** The AI will greet you automatically
6. **Click "Voice Active" button** if auto-listen didn't start
7. **Speak clearly** and wait for 1.5 second pause

## Still Not Working?

### Check This Checklist:

- [ ] You clicked on "🎤 Voice Assistant" in the sidebar
- [ ] You granted microphone permission
- [ ] You can see the animated voice visualization
- [ ] The button says "Voice Active" (not "Voice Paused")
- [ ] Your microphone is working in other apps
- [ ] You're using Chrome or Firefox (not Safari)
- [ ] No JavaScript errors in browser console
- [ ] Backend logs show voice session creation

### Get Help

If still not working, provide:

1. Browser console errors (F12 → Console tab)
2. Backend logs (look for voice-related errors)
3. Microphone permission status
4. Browser and OS information

## Contact Backend API Directly

Test if the backend voice orchestration works:

```bash
# Test with a simple session creation
curl -s http://localhost:8000/api/voice/session -X POST \
  -H "Content-Type: application/json" -d '{"user_id": "test"}'
  
# Should return:
{
  "session_id": "uuid-here",
  "created_at": "timestamp",
  "turn_count": 0,
  "status": "active"
}
```

If this works but the frontend doesn't, the issue is in the browser/frontend.
