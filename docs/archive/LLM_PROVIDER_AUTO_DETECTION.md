# 🤖 LLM Provider Auto-Detection & Smart Fallback

## 🎯 Overview

The LLM provider system now intelligently detects configured providers from your `.env` file and automatically handles fallback logic based on what's available.

---

## 🔍 How It Works

### **3 Operating Modes**

#### **1. No Providers Configured** ❌
**Behavior**: Raises an error immediately

```bash
# .env (missing credentials)
# AZURE_OPENAI_ENDPOINT=
# AZURE_OPENAI_API_KEY=
# TOGETHER_API_KEY=
```

**Result**:
```
❌ ERROR: No LLM providers configured. Please set one of:
   • Azure: AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY
   • Together AI: TOGETHER_API_KEY
```

---

#### **2. Single Provider Configured** ✅
**Behavior**: Uses that provider exclusively (no fallback)

**Example: Azure Only**
```bash
# .env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
# TOGETHER_API_KEY= (not set)
```

**Result**:
```
✅ Only Azure configured - using Azure exclusively (no fallback)
   • Active provider: AzureOpenAIProvider
   • Fallback: None
```

**Example: Together AI Only**
```bash
# .env
TOGETHER_API_KEY=your-together-key
# AZURE_OPENAI_ENDPOINT= (not set)
# AZURE_OPENAI_API_KEY= (not set)
```

**Result**:
```
✅ Only Together AI configured - using Together exclusively (no fallback)
   • Active provider: TogetherAIProvider
   • Fallback: None
```

---

#### **3. Both Providers Configured** ✅✅
**Behavior**: Smart fallback enabled

```bash
# .env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key
TOGETHER_API_KEY=your-together-key
```

**Result**:
```
✅ Both Azure and Together AI configured - fallback enabled
   • Primary: Azure OpenAI (or Together AI if specified)
   • Fallback: Together AI (or Azure OpenAI)
   • Auto-switch: If primary fails
```

---

## 🎛️ Provider Selection Modes

### **Mode 1: Auto-Detection** (Recommended)
```python
# In .env
LLM_PROVIDER=auto

# Or in code
from shared.llm import llm_client

# Will auto-detect and prefer Azure if both configured
```

**Behavior**:
- Detects configured providers from `.env`
- Prefers **Azure** if both are configured
- Falls back to **Together AI** if Azure fails
- Raises error if none configured

---

### **Mode 2: Azure Primary**
```python
# In .env
LLM_PROVIDER=azure

# Or in code
client = get_llm_client(provider_type="azure", ...)
```

**Behavior**:
- Uses Azure as primary
- Falls back to Together AI (if configured)
- No fallback if only Azure configured
- Error if Azure not configured

---

### **Mode 3: Together AI Primary**
```python
# In .env
LLM_PROVIDER=together

# Or in code
client = get_llm_client(provider_type="together", ...)
```

**Behavior**:
- Uses Together AI as primary
- Falls back to Azure (if configured)
- No fallback if only Together AI configured
- Error if Together AI not configured

---

## 📊 Configuration Matrix

| Azure | Together | Provider Type | Result |
|-------|----------|---------------|---------|
| ❌ | ❌ | auto/azure/together | ❌ **ERROR** - No providers |
| ✅ | ❌ | auto/azure | ✅ **Azure only** - No fallback |
| ✅ | ❌ | together | ❌ **ERROR** - Together not configured |
| ❌ | ✅ | auto/together | ✅ **Together only** - No fallback |
| ❌ | ✅ | azure | ❌ **ERROR** - Azure not configured |
| ✅ | ✅ | auto | ✅ **Azure primary**, Together fallback |
| ✅ | ✅ | azure | ✅ **Azure primary**, Together fallback |
| ✅ | ✅ | together | ✅ **Together primary**, Azure fallback |

---

## 🛠️ Configuration Examples

### **Example 1: Production (Azure Only)**
```bash
# .env - Production setup with Azure only
LLM_PROVIDER=azure  # or "auto" (will detect Azure)
AZURE_OPENAI_ENDPOINT=https://prod-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=prod-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2025-04-14
```

**Behavior**: Azure exclusively, no fallback, enterprise-grade

---

### **Example 2: Development (Together AI Only)**
```bash
# .env - Dev setup with Together AI only
LLM_PROVIDER=together  # or "auto" (will detect Together)
TOGETHER_API_KEY=dev-key-here
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
```

**Behavior**: Together AI exclusively, no fallback, cost-effective

---

### **Example 3: High Availability (Both Providers)**
```bash
# .env - HA setup with both providers
LLM_PROVIDER=auto  # or "azure" or "together"
AZURE_OPENAI_ENDPOINT=https://prod-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=azure-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
TOGETHER_API_KEY=together-key-here
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
```

**Behavior**: Azure primary, Together fallback, maximum reliability

---

## 🧪 Testing

### **Test Current Configuration**
```bash
# Run the auto-detection test
python test_llm_provider_auto_detection.py
```

**Output**:
```
📋 Configured Providers:
   • Azure OpenAI:  ✅ Yes
   • Together AI:   ✅ Yes

📊 Total Configured: 2
   ✅ Multiple providers - fallback enabled
```

---

### **Test in Code**
```python
from shared.llm_providers.factory import LLMFactory
from shared.config import settings

# Detect configured providers
configured = LLMFactory.detect_configured_providers(
    azure_endpoint=settings.azure_openai_endpoint,
    azure_api_key=settings.azure_openai_api_key,
    together_api_key=settings.together_api_key
)

print(f"Azure configured: {configured['azure']}")
print(f"Together configured: {configured['together']}")
```

---

## 🔄 Fallback Flow Diagram

```
User Request
    ↓
[Auto-Detect Configured Providers]
    ↓
┌─────────────┬────────────────┬─────────────┐
│ None        │ Single         │ Both        │
│ Configured  │ Configured     │ Configured  │
└─────────────┴────────────────┴─────────────┘
    ↓               ↓                ↓
  ERROR         Use Exclusively   Enable Fallback
                (No Fallback)
                    ↓                ↓
                ┌───────┐       ┌───────────┐
                │ Azure │       │ Primary   │
                │  or   │       │ Provider  │
                │Together│      └───────────┘
                └───────┘            ↓
                    ↓          ┌──────────┐
                    ↓          │Available?│
                    ↓          └──────────┘
                    ↓           ↓        ↓
                    ↓         YES       NO
                    ↓          ↓         ↓
                    ↓       SUCCESS  Try Fallback
                    ↓                    ↓
                    ↓              ┌──────────┐
                    ↓              │Available?│
                    ↓              └──────────┘
                    ↓               ↓        ↓
                    ↓             YES       NO
                    ↓              ↓         ↓
                    └────────→ SUCCESS    ERROR
```

---

## 📝 Code Examples

### **Example 1: Use Current Configuration**
```python
from shared.llm import llm_client

# Uses provider from .env (auto-detected)
response = await llm_client.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

### **Example 2: Force Specific Provider**
```python
from shared.llm_providers import get_llm_client

# Force Azure (will error if not configured)
azure_client = get_llm_client(
    provider_type="azure",
    azure_endpoint="...",
    azure_api_key="..."
)

# Force Together AI (will error if not configured)
together_client = get_llm_client(
    provider_type="together",
    together_api_key="..."
)
```

---

### **Example 3: Auto-Detection with Logging**
```python
from shared.llm_providers import get_llm_client
import logging

logging.basicConfig(level=logging.INFO)

# Will log the detection process
client = get_llm_client(provider_type="auto", ...)

# Example output:
# ✅ Both Azure and Together AI configured - fallback enabled
#    • Auto-detection: Using azure as primary
#    • ✅ Azure OpenAI is available (primary)
#    • 🔄 Together AI ready as fallback
```

---

## 🚨 Error Messages

### **No Providers Configured**
```
❌ No LLM providers configured. Please set one of:
   • Azure: AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY
   • Together AI: TOGETHER_API_KEY
```

**Solution**: Add credentials to `.env`

---

### **Provider Not Available**
```
❌ Azure OpenAI configured but not available. Check credentials.
```

**Solution**: Verify API key, endpoint, and deployment name

---

### **Both Providers Failed**
```
❌ Both Azure OpenAI and Together AI failed to initialize
```

**Solution**: Check network, credentials, and service status

---

## 🎯 Best Practices

### **1. Production: Single Provider**
- Use Azure only for reliability and compliance
- No fallback complexity
- Easier to debug

```bash
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
```

---

### **2. Development: Cost-Effective**
- Use Together AI for development
- Lower costs
- Fast iteration

```bash
LLM_PROVIDER=together
TOGETHER_API_KEY=...
```

---

### **3. High Availability: Both Providers**
- Configure both for maximum uptime
- Auto-fallback on failure
- Monitor which provider is active

```bash
LLM_PROVIDER=auto
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
TOGETHER_API_KEY=...
```

---

## 🔍 Troubleshooting

### **Issue: "Auto-detection using together instead of azure"**
**Cause**: Azure credentials invalid or endpoint unreachable

**Solution**:
1. Verify Azure credentials in `.env`
2. Test Azure endpoint: `curl https://your-endpoint/`
3. Check deployment name matches

---

### **Issue: "No fallback happening when primary fails"**
**Cause**: Only one provider configured

**Solution**:
```bash
# Add both providers to .env
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
TOGETHER_API_KEY=...
```

---

### **Issue: "Want to disable fallback"**
**Solution**: Remove one provider from `.env`

```bash
# To use Azure only (no fallback)
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
# TOGETHER_API_KEY= (comment out or remove)
```

---

## 📊 Monitoring

### **Check Active Provider**
```python
from shared.llm import llm_client

provider_name = type(llm_client.provider).__name__
print(f"Active: {provider_name}")
# Output: AzureOpenAIProvider or TogetherAIProvider
```

---

### **Log Provider Usage**
```python
import logging

logging.basicConfig(level=logging.INFO)

# Logs will show provider selection:
# ✅ Both Azure and Together AI configured - fallback enabled
#    • Azure OpenAI is available (primary)
```

---

## 🎉 Summary

**New Capabilities**:
- ✅ Auto-detects configured providers
- ✅ Smart fallback only when multiple providers available
- ✅ Clear error messages when nothing configured
- ✅ Single provider mode (no fallback overhead)
- ✅ Multi-provider mode (high availability)
- ✅ Configuration-driven (no code changes needed)

**Migration**: No code changes required! Just update `.env` and the system adapts automatically.

---

**Last Updated**: October 22, 2025  
**Version**: 2.0 - Smart Auto-Detection
