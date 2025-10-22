# Azure Integration - Quick Reference Guide

## 🚀 Quick Start

### **Check Current Provider**
```python
from shared.config import settings

print(f"Current LLM Provider: {settings.llm_provider}")
# Output: Current LLM Provider: azure
```

### **Test LLM Client**
```python
from shared.llm import llm_client

# Simple chat completion
response = await llm_client.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response)
```

### **Test Input Routing**
```python
from shared.routing import InputRouter, InputType
from shared.azure_services import azure_speech_service

router = InputRouter(speech_service=azure_speech_service)

# Route text input
result = await router.route({
    "type": "text",
    "content": "Fix the bug in main.py"
})
print(result["text"])
```

### **Test Intent Classification**
```python
from shared.routing import IntentClassifier

classifier = IntentClassifier()

# Classify query
result = classifier.classify("Analyze issue #123")
print(f"Repo-related: {result['is_repo_related']}")
print(f"Confidence: {result['confidence']:.2f}")
```

---

## 📋 Environment Variables

### **Azure OpenAI (Primary Provider)**
```bash
# Required
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2025-04-14

# Optional
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### **Together AI (Fallback Provider)**
```bash
# Optional (for fallback)
TOGETHER_API_KEY=your-together-api-key
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
```

### **Azure Speech Services**
```bash
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=eastus2
AZURE_SPEECH_LANG=en-US
```

### **Provider Selection**
```bash
# Default: azure
LLM_PROVIDER=azure

# Override to Together AI
# LLM_PROVIDER=together

# Role-based overrides
CHAT_PROVIDER=azure
EMBEDDING_PROVIDER=azure
BEAUTIFY_PROVIDER=azure
```

---

## 🔧 Common Use Cases

### **1. Switch to Together AI**
```bash
# In .env
LLM_PROVIDER=together
```

### **2. Force Azure Even if Together AI is Available**
```bash
# In .env
LLM_PROVIDER=azure
```

### **3. Use Azure for Chat, Together AI for Embeddings**
```bash
# In .env
CHAT_PROVIDER=azure
EMBEDDING_PROVIDER=together
```

### **4. Disable Fallback (Azure Only)**
```bash
# Don't set TOGETHER_API_KEY
# If Azure fails, request will fail (no fallback)
```

---

## 🧪 Testing

### **Test Provider Availability**
```python
from shared.llm_providers import get_llm_client

# Test Azure
azure_client = get_llm_client(
    provider_type="azure",
    azure_endpoint=settings.azure_openai_endpoint,
    azure_api_key=settings.azure_openai_api_key
)
print(f"Azure available: {azure_client.is_available()}")

# Test Together AI
together_client = get_llm_client(
    provider_type="together",
    together_api_key=settings.together_api_key
)
print(f"Together AI available: {together_client.is_available()}")
```

### **Test Fallback Mechanism**
```python
# Set invalid Azure credentials temporarily
import os
os.environ["AZURE_OPENAI_API_KEY"] = "invalid"

# Factory should fallback to Together AI
client = get_llm_client(
    provider_type="azure",
    together_api_key=settings.together_api_key
)
print(f"Active provider: {type(client).__name__}")
# Output: TogetherAIProvider (fallback activated)
```

### **Test Voice Input Pipeline**
```python
import base64

# Prepare voice input
with open("audio.webm", "rb") as f:
    audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode()

# Route voice input
result = await router.route({
    "type": "voice",
    "content": audio_base64,
    "format": "webm"
})

print(f"Transcribed: {result['text']}")
print(f"Language: {result['language']}")
```

---

## 🐛 Troubleshooting

### **Issue: "Azure OpenAI client not initialized"**
**Cause**: Missing or invalid Azure credentials

**Solution**:
```bash
# Check .env file
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=...

# Or check environment variables
echo $env:AZURE_OPENAI_ENDPOINT
echo $env:AZURE_OPENAI_API_KEY
```

### **Issue: "LLM provider 'azure' not available"**
**Cause**: Azure credentials not configured or invalid

**Solution**:
1. Verify credentials in `.env`
2. Check Azure resource is deployed
3. Verify deployment name matches
4. Check API key has correct permissions

### **Issue: "Speech service not configured"**
**Cause**: Missing Azure Speech credentials

**Solution**:
```bash
# Add to .env
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=eastus2
```

### **Issue: Fallback not working**
**Cause**: Fallback provider not configured

**Solution**:
```bash
# Add Together AI credentials for fallback
TOGETHER_API_KEY=your-together-api-key
```

---

## 📊 Monitoring

### **Check Active Provider**
```python
from shared.llm import llm_client

if llm_client.provider:
    provider_type = type(llm_client.provider).__name__
    print(f"Active provider: {provider_type}")
else:
    print("No provider available")
```

### **Log Provider Usage**
```python
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)

# LLM requests will log provider info
response = await llm_client.chat_completion(
    messages=[{"role": "user", "content": "Test"}]
)
# Logs: "✅ LLM client initialized with provider: azure"
```

### **Track Fallback Events**
```python
# Check logs for fallback warnings
# "⚠️  Azure provider not available, trying fallback"
# "Falling back to Together AI"
```

---

## 🔄 Migration Checklist

- [x] Azure set as default provider
- [x] Factory defaults updated
- [x] Config defaults updated
- [x] Input router created
- [x] Intent classifier created
- [x] Documentation created
- [ ] Embedding service updated
- [ ] API endpoints updated
- [ ] UI components updated
- [ ] Tests updated
- [ ] Production deployment

---

## 📚 Code Examples

### **Full Voice-to-Voice Example**
```python
from shared.routing import InputRouter, IntentClassifier
from shared.azure_services import azure_speech_service
from shared.llm import llm_client
import base64

# 1. Setup
router = InputRouter(speech_service=azure_speech_service)
classifier = IntentClassifier()

# 2. Process voice input
voice_data = base64.b64encode(open("input.webm", "rb").read()).decode()
routed = await router.route({
    "type": "voice",
    "content": voice_data,
    "format": "webm"
})

# 3. Classify intent
intent = classifier.classify(routed["text"])

# 4. Generate response
if intent["is_repo_related"]:
    # Query Qdrant backend
    response = await query_qdrant(routed["text"])
else:
    # Use Azure OpenAI
    response = await llm_client.chat_completion(
        messages=[{"role": "user", "content": routed["text"]}]
    )

# 5. Synthesize speech
audio_output = await azure_speech_service.synthesize_speech(
    text=response,
    output_file_path="output.wav"
)

print(f"✅ Voice-to-Voice complete!")
```

### **Custom Provider Configuration**
```python
from shared.llm_providers import LLMFactory

# Create custom Azure client
azure_client = LLMFactory.create_provider(
    provider_type="azure",
    azure_endpoint="https://custom-endpoint.openai.azure.com/",
    azure_api_key="custom-key",
    azure_deployment="gpt-4o",
    azure_api_version="2024-05-01"
)

# Use custom client
response = await azure_client.chat_completion(
    messages=[{"role": "user", "content": "Hello"}]
)
```

---

## 🎯 Best Practices

1. **Always use environment variables** for credentials
2. **Enable logging** for debugging provider issues
3. **Configure fallback** for production reliability
4. **Monitor provider usage** to optimize costs
5. **Test both providers** before deployment
6. **Use intent classification** to route queries efficiently
7. **Implement retry logic** for transient failures
8. **Cache embeddings** to reduce API calls

---

## 🔗 Related Documentation

- [`INTEGRATION_PLAN.md`](./INTEGRATION_PLAN.md) - Full integration plan
- [`AZURE_MIGRATION_PLAN.md`](./AZURE_MIGRATION_PLAN.md) - Detailed migration guide
- [`ARCHITECTURE_DIAGRAMS.md`](./ARCHITECTURE_DIAGRAMS.md) - Visual architecture
- [`IMPLEMENTATION_STATUS.md`](./IMPLEMENTATION_STATUS.md) - Current status

---

**Last Updated**: October 22, 2025  
**Maintained by**: Development Team
