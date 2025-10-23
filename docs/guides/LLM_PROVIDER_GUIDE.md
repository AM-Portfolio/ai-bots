# LLM Provider Guide

## Overview

The AI Development Agent now supports **multiple LLM providers** through a clean factory pattern architecture. **Together AI is the default provider**, with Azure OpenAI available as an alternative.

---

## Architecture

### Factory Pattern Design

```
┌─────────────────────────────────────┐
│         LLM Client (llm.py)         │
│  Unified interface for all services │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│      LLM Factory (factory.py)       │
│   Creates provider based on config   │
└──────────────┬──────────────────────┘
               │
        ┌──────┴───────┐
        ↓              ↓
┌──────────────┐  ┌──────────────────┐
│  Together AI │  │  Azure OpenAI    │
│   Provider   │  │     Provider     │
└──────────────┘  └──────────────────┘
```

### Components

1. **Base Provider** (`shared/llm_providers/base.py`)
   - Abstract interface defining standard LLM operations
   - Methods: `chat_completion`, `analyze_code`, `generate_tests`, `generate_documentation`

2. **Together AI Provider** (`shared/llm_providers/together_provider.py`)
   - Default implementation using Together AI
   - Model: `meta-llama/Llama-3.3-70B-Instruct-Turbo`
   - Fast, cost-effective, open-source models

3. **Azure OpenAI Provider** (`shared/llm_providers/azure_provider.py`)
   - Alternative implementation using Azure OpenAI
   - Model: GPT-4 (configurable)
   - Enterprise-grade, Microsoft-backed

4. **Factory** (`shared/llm_providers/factory.py`)
   - Creates provider instances based on configuration
   - Handles fallback logic automatically
   - Supports provider switching without code changes

5. **Unified Client** (`shared/llm.py`)
   - Single interface for all application services
   - Transparent provider switching
   - Automatic error handling and fallback

---

## Configuration

### Default: Together AI

```env
# Set provider type (default: together)
LLM_PROVIDER=together

# Together AI credentials
TOGETHER_API_KEY=your-together-api-key
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
```

### Alternative: Azure OpenAI

```env
# Switch to Azure OpenAI
LLM_PROVIDER=azure

# Azure OpenAI credentials
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Automatic Fallback

The system automatically tries the fallback provider if the primary one fails:

1. **Primary**: Together AI (if configured)
2. **Fallback**: Azure OpenAI (if Together AI unavailable)

```env
# Configure both for automatic fallback
LLM_PROVIDER=together
TOGETHER_API_KEY=your-together-key
AZURE_OPENAI_ENDPOINT=https://your-azure.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key
```

---

## Getting API Keys

### Together AI (Recommended)

1. **Sign Up**: Visit [Together AI Platform](https://api.together.xyz/)
2. **Create Account**: Free tier available
3. **Get API Key**:
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Copy the key to your `.env` file

**Benefits:**
- ✅ No Azure subscription required
- ✅ Fast inference speeds
- ✅ Open-source models
- ✅ Cost-effective pricing
- ✅ Simple setup

### Azure OpenAI (Alternative)

1. **Azure Portal**: [portal.azure.com](https://portal.azure.com)
2. **Create Resource**: Search for "Azure OpenAI"
3. **Deploy Model**: Create GPT-4 deployment
4. **Get Credentials**:
   - Navigate to resource → Keys and Endpoint
   - Copy endpoint URL and API key

**Benefits:**
- ✅ Enterprise support
- ✅ Microsoft SLA
- ✅ Azure integration
- ✅ Compliance certifications

---

## Available Models

### Together AI Models

| Model | Description | Best For |
|-------|-------------|----------|
| `meta-llama/Llama-3.3-70B-Instruct-Turbo` | Default, best balance | General use |
| `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` | Faster, smaller | Quick responses |
| `deepseek/DeepSeek-R1` | Advanced reasoning | Complex analysis |
| `Qwen/Qwen2.5-72B-Instruct-Turbo` | High quality | Critical tasks |

**Update model in .env:**
```env
TOGETHER_MODEL=deepseek/DeepSeek-R1
```

### Azure OpenAI Models

| Model | Description | Best For |
|-------|-------------|----------|
| `gpt-4` | Most capable | Complex tasks |
| `gpt-4-turbo` | Faster GPT-4 | General use |
| `gpt-35-turbo` | Cost-effective | Simple tasks |

**Update deployment in .env:**
```env
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-turbo
```

---

## Usage Examples

### Code Analysis

```python
from shared.llm import llm_client

# Works with any configured provider
result = await llm_client.analyze_code(
    code="def buggy_function(): ...",
    context="User login system",
    task="find bugs"
)
```

### Test Generation

```python
tests = await llm_client.generate_tests(
    code="def calculate_total(items): ...",
    language="python"
)
```

### Documentation

```python
docs = await llm_client.generate_documentation(
    content="API endpoint details...",
    doc_type="confluence"
)
```

### Chat Completion

```python
response = await llm_client.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Explain this error..."}
    ],
    temperature=0.7
)
```

---

## Provider Comparison

| Feature | Together AI | Azure OpenAI |
|---------|-------------|--------------|
| **Setup Complexity** | Simple | Moderate |
| **Cost** | Lower | Higher |
| **Speed** | Very Fast | Fast |
| **Models** | Open-source | GPT-4, GPT-3.5 |
| **Azure Required** | No | Yes |
| **Enterprise Support** | Community | Microsoft SLA |
| **Compliance** | Standard | Enterprise-grade |
| **API Compatibility** | OpenAI-compatible | Native OpenAI |

---

## Switching Providers

### At Runtime (via config)

Change `.env` and restart:
```env
# Before
LLM_PROVIDER=together

# After
LLM_PROVIDER=azure
```

### Programmatically

```python
from shared.llm_providers import get_llm_client

# Create specific provider
together_client = get_llm_client(
    provider_type="together",
    together_api_key="your-key"
)

azure_client = get_llm_client(
    provider_type="azure",
    azure_endpoint="https://...",
    azure_api_key="your-key"
)
```

---

## Troubleshooting

### "Together AI API key not configured"

**Solution:**
```env
TOGETHER_API_KEY=your-actual-api-key
```

### "LLM provider 'together' not available"

**Causes:**
1. Missing API key
2. Invalid API key
3. Network issues

**Solution:**
- Check `.env` file has `TOGETHER_API_KEY`
- Verify key is valid at [Together AI](https://api.together.xyz/)
- Check network connectivity

### Automatic Fallback

If you see:
```
Together provider not available, trying fallback
```

The system is automatically switching to Azure OpenAI. Ensure Azure credentials are configured if you want fallback to work.

### No Provider Available

**Error:**
```
No LLM provider available
```

**Solution:**
Configure at least one provider:
```env
# Option 1: Together AI
TOGETHER_API_KEY=your-key

# Option 2: Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=your-key

# Option 3: Both (recommended)
TOGETHER_API_KEY=your-together-key
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=your-azure-key
```

---

## Best Practices

### 1. Use Together AI as Primary

Together AI offers the best balance of speed, cost, and quality:
```env
LLM_PROVIDER=together
TOGETHER_API_KEY=your-key
```

### 2. Configure Fallback

Always configure both providers for reliability:
```env
TOGETHER_API_KEY=your-together-key
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=your-azure-key
```

### 3. Select Appropriate Models

**For speed:**
```env
TOGETHER_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

**For quality:**
```env
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
```

**For reasoning:**
```env
TOGETHER_MODEL=deepseek/DeepSeek-R1
```

### 4. Monitor Usage

Check logs for provider usage:
```bash
grep "LLM" /tmp/logs/Server_*.log
```

---

## Migration Guide

### From Azure OpenAI Only

**Before:**
```env
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=your-key
```

**After (with Together AI):**
```env
LLM_PROVIDER=together
TOGETHER_API_KEY=your-together-key

# Keep Azure as fallback
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=your-azure-key
```

### No Code Changes Required

The factory pattern handles everything automatically. All existing code continues to work with any provider.

---

## Future Providers

The factory pattern makes it easy to add new providers:

1. Create provider class implementing `BaseLLMProvider`
2. Add to factory `create_provider` method
3. Update configuration

**Potential additions:**
- OpenAI (direct)
- Anthropic Claude
- Google Gemini
- Cohere
- Local LLMs (Ollama)

---

## Summary

✅ **Together AI is now the default LLM provider**  
✅ **Azure OpenAI remains available as alternative**  
✅ **Factory pattern enables easy provider switching**  
✅ **Automatic fallback for reliability**  
✅ **No code changes needed to switch providers**  
✅ **Better performance and cost with Together AI**  

Get started: Add `TOGETHER_API_KEY` to your `.env` file and you're ready to go!
