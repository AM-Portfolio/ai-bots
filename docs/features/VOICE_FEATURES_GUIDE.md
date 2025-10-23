# Voice Features Guide

## 🎙️ Voice Assistance Overview

Your AI Dev Agent now supports **voice input** and **voice output** for a hands-free, conversational experience!

## Features

### 1. 🎤 Voice Input (Speech-to-Text)
- **Click the microphone button** to start voice input
- Speak your question or prompt
- Your speech is automatically converted to text
- Works in modern browsers (Chrome, Edge, Safari)

### 2. 🔊 Voice Response (Text-to-Speech)
- **Toggle "Voice Response"** to enable voice output
- AI responses are automatically spoken aloud
- Uses natural browser voices
- Adjustable speed, pitch, and volume

### 3. ✨ Thinking Mode
- **Toggle "Thinking Mode"** for a clean chat experience
- Hides verbose backend details
- Shows only essential messages
- Perfect for focused conversations

## How to Use

### Voice Input

1. **Start Voice Input:**
   - Click the **microphone button** in the text input area
   - Button turns red when listening
   - Speak clearly into your microphone

2. **Stop Listening:**
   - Click the microphone button again (now red with MicOff icon)
   - Voice input automatically stops after speech detection

3. **Visual Feedback:**
   - Red border around text area when listening
   - "🎤 Listening... Speak now" message appears
   - Textarea shows "Listening..." placeholder

### Voice Response

1. **Enable Voice Output:**
   - Check the **"Voice Response"** toggle in Settings
   - Volume icon indicates voice is enabled
   - Blue indicator shows "Voice responses enabled"

2. **Automatic Playback:**
   - AI responses are automatically spoken
   - Voice starts playing immediately after response
   - Natural, browser-native voices

3. **Disable Voice Output:**
   - Uncheck "Voice Response" toggle
   - Responses appear as text only

### Thinking Mode

1. **Enable Thinking Mode:**
   - Check the **"Thinking Mode" (✨)** toggle
   - Hides verbose backend processing details
   - Shows clean "Thinking..." message

2. **Clean Chat Window:**
   - Fewer lines of text
   - Focus on conversation
   - No technical backend steps shown

3. **Disable for Details:**
   - Uncheck to see full backend processing
   - Shows all 3 processing steps
   - Useful for debugging

## Technology

### Voice Input (Speech Recognition)
- **API:** Web Speech API (browser-native)
- **Cost:** Free (no API key needed)
- **Supported Browsers:**
  - ✅ Chrome/Edge (best support)
  - ✅ Safari (iOS/macOS)
  - ⚠️ Firefox (limited support)
- **Languages:** English (en-US) by default

### Voice Output (Speech Synthesis)
- **API:** Web Speech Synthesis API (browser-native)
- **Cost:** Free (no API key needed)
- **Voices:** System voices (varies by OS)
- **Quality:** Good for conversational use
- **Latency:** Instant (no server round-trip)

## Settings Breakdown

| Setting | Icon | Purpose |
|---------|------|---------|
| **Voice Response** | 🔊 | Enable/disable voice output |
| **Thinking Mode** | ✨ | Hide verbose backend details |
| **Backend Details** | (checkbox) | Show full processing steps |

## Use Cases

### 1. Hands-Free Development
- Ask questions while coding
- Get spoken answers without looking away
- Perfect for multitasking

### 2. Accessibility
- Voice input for typing assistance
- Voice output for screen-free interaction
- Helpful for visual impairments

### 3. Learning & Understanding
- Listen to explanations while reading code
- Ask follow-up questions via voice
- Natural conversation flow

### 4. Clean Chat Experience
- Enable Thinking Mode for minimal UI
- Focus on conversation content
- Less visual clutter

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Send message | `Enter` |
| New line | `Shift + Enter` |
| Voice input | Click mic button |

## Browser Compatibility

### Voice Input (Speech Recognition)
| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Best experience |
| Edge | ✅ Full | Chromium-based |
| Safari | ✅ Full | iOS 14.5+ |
| Firefox | ❌ Limited | Not supported |
| Opera | ✅ Full | Chromium-based |

### Voice Output (Speech Synthesis)
| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Multiple voices |
| Edge | ✅ Full | High-quality voices |
| Safari | ✅ Full | Natural voices |
| Firefox | ✅ Full | Good support |
| Opera | ✅ Full | Multiple voices |

## Troubleshooting

### Voice Input Not Working

**Issue:** Microphone button doesn't activate
- **Solution:** Check browser permissions
- Go to browser settings → Site permissions → Microphone
- Allow microphone access for this site

**Issue:** No speech detected
- **Solution:** Check microphone settings
- Ensure microphone is connected and working
- Test in system settings
- Try a different browser

**Issue:** Wrong language detected
- **Solution:** Currently set to English (en-US)
- Can be customized in code if needed

### Voice Output Not Working

**Issue:** No audio playback
- **Solution:** Check volume settings
- Ensure system volume is not muted
- Check browser audio permissions
- Try refreshing the page

**Issue:** Voice sounds robotic
- **Solution:** Browser-dependent voice quality
- Chrome/Edge have better voices
- Install additional system voices for improvement

**Issue:** Voice cuts off mid-sentence
- **Solution:** Browser limitation
- Usually resolves on retry
- Try shorter responses

### Thinking Mode Issues

**Issue:** Still seeing backend details
- **Solution:** Ensure both toggles are set correctly
- Thinking Mode ON = hides details
- Backend Details OFF = no verbose output

## Privacy & Security

### Voice Input
- ✅ Processed by browser (Chrome uses Google's servers)
- ✅ Not stored permanently
- ✅ Only sent when microphone is active
- ⚠️ Check browser's privacy policy

### Voice Output
- ✅ Fully client-side (browser-native)
- ✅ No server transmission
- ✅ Private and secure
- ✅ No API key required

## Advanced Customization

### Voice Settings (Code-Level)

**Speech Recognition Settings:**
```typescript
recognitionRef.current.continuous = false;  // Single utterance
recognitionRef.current.interimResults = false;  // No interim results
recognitionRef.current.lang = 'en-US';  // Language
```

**Speech Synthesis Settings:**
```typescript
utterance.rate = 1.0;  // Speed (0.1-10)
utterance.pitch = 1.0;  // Pitch (0-2)
utterance.volume = 1.0;  // Volume (0-1)
```

### Changing Voice (Browser Console)

```javascript
// List available voices
window.speechSynthesis.getVoices();

// Select a voice
const voices = window.speechSynthesis.getVoices();
const femaleVoice = voices.find(v => v.name.includes('Female'));
utterance.voice = femaleVoice;
```

## Future Enhancements

### Planned Features
- [ ] Multiple language support
- [ ] Voice selection UI
- [ ] Custom wake word detection
- [ ] Voice activity visualization
- [ ] Export voice conversations
- [ ] Voice commands (e.g., "clear chat")

### Premium Voice Options (If Needed)
If you need higher quality voices:
- **ElevenLabs:** Ultra-realistic, emotion control
- **Google Cloud TTS:** 380+ voices, 50+ languages
- **OpenAI TTS:** Natural, conversational voices
- **Azure Speech:** Neural voices, 140+ languages

Currently using **free browser-native voices** for zero cost!

## Best Practices

### For Voice Input
1. ✅ Speak clearly and at normal pace
2. ✅ Minimize background noise
3. ✅ Use short, focused questions
4. ✅ Wait for "Listening..." indicator

### For Voice Output
1. ✅ Enable in quiet environments
2. ✅ Test volume before long conversations
3. ✅ Disable for technical/code-heavy responses
4. ✅ Use headphones for privacy

### For Thinking Mode
1. ✅ Enable for casual conversations
2. ✅ Disable when debugging issues
3. ✅ Toggle based on your workflow
4. ✅ Combine with voice for hands-free mode

## FAQ

**Q: Is voice input free?**
A: Yes, uses browser's built-in Speech API (no cost)

**Q: Does it work offline?**
A: Voice output works offline. Voice input may require internet (browser-dependent)

**Q: Can I use other languages?**
A: Currently English only. Can be customized in code

**Q: Is my voice data stored?**
A: No permanent storage. Browser may send to its servers for processing (check browser privacy policy)

**Q: Can I adjust voice speed?**
A: Yes, in code settings (default 1.0x speed)

**Q: Does it work on mobile?**
A: Yes! Both iOS Safari and Chrome mobile support voice features

---

**Enjoy your hands-free AI development experience!** 🎙️✨
