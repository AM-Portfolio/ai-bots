# Cloud-Agnostic Orchestration Architecture

## Overview

This document describes the **cloud-agnostic orchestration layer** that enables seamless switching between AI cloud providers (Azure, Together AI, OpenAI) with automatic fallback and unified interfaces.

## Architecture Goals

1. **Cloud-Agnostic**: Use any provider without changing application code
2. **Template-Based**: Modular provider implementations following standard interfaces
3. **Automatic Fallback**: Resilient service with multi-provider fallback chains
4. **Easy Migration**: Switch providers with simple configuration changes
5. **Future-Scalable**: Add new providers without touching existing code

---

## Architecture Components

### 1. Provider Templates (`orchestration/cloud_providers/templates/base.py`)

**Abstract base classes** defining standard interfaces for all cloud providers:

```python
# Core provider capabilities
class ProviderCapability(Enum):
    SPEECH_TO_TEXT = "stt"
    TEXT_TO_SPEECH = "tts"
    TRANSLATION = "translation"
    LLM_CHAT = "llm_chat"
    LLM_EMBEDDING = "llm_embedding"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    DIARIZATION = "diarization"

# Standard interfaces
class STTProvider(ABC):         # Speech-to-Text
class TTSProvider(ABC):         # Text-to-Speech
class TranslationProvider(ABC): # Translation
class LLMProvider(ABC):         # LLM Chat & Embeddings
```

**Result types** with standardized metadata:

```python
@dataclass
class STTResult:
    text: str
    detected_language: Optional[str]
    confidence: Optional[float]
    duration_ms: Optional[float]
    method: Optional[str]
    metadata: Optional[Dict[str, Any]]
```

---

### 2. Provider Implementations (`orchestration/cloud_providers/implementations/`)

Each provider implements the standard templates:

#### **Azure Provider** (`azure_provider.py`)
Wraps existing Azure AI services:
- **STT**: Azure Speech Service
- **TTS**: Azure Speech Service  
- **Translation**: Azure Translator
- **LLM**: Azure OpenAI (GPT models)
- **Embeddings**: Azure OpenAI

#### **Together AI Provider** (`together_provider.py`)
Implements LLM capabilities:
- **LLM**: Together AI (Llama models)
- **Embeddings**: Together AI

#### **OpenAI Provider** (`openai_provider.py`)
Implements OpenAI services:
- **STT**: Whisper
- **TTS**: OpenAI TTS
- **LLM**: GPT models

---

### 3. Provider Factory (`orchestration/cloud_providers/factory.py`)

**Factory pattern** for creating provider instances:

```python
from orchestration.cloud_providers.factory import ProviderFactory

# Create a provider
provider = ProviderFactory.create_provider(
    provider_name="azure",      # or "together", "openai"
    capability=ProviderCapability.SPEECH_TO_TEXT,
    config=None                 # Auto-detected from ENV
)

# Check available providers for a capability
available = ProviderFactory.get_available_providers(
    ProviderCapability.LLM_CHAT
)
```

**Auto-detection** from environment variables:
- Azure: `AZURE_OPENAI_KEY`, `AZURE_SPEECH_KEY`, `AZURE_TRANSLATION_KEY`
- Together AI: `TOGETHER_API_KEY`
- OpenAI: `OPENAI_API_KEY`

**Fallback chains** based on configuration:
- LLM Chat: `Azure → Together AI → OpenAI`
- STT: `Azure → OpenAI`
- TTS: `OpenAI → Azure`
- Translation: `Azure` (primary)

---

### 4. Orchestration Manager (`orchestration/cloud_providers/orchestrator.py`)

**Central coordinator** that routes requests to appropriate providers:

```python
from orchestration.cloud_providers.orchestrator import orchestrator

# Speech-to-Text with automatic fallback
result = await orchestrator.speech_to_text(
    audio_data=audio_bytes,
    audio_format="wav",
    preferred_provider="azure"  # Optional: force specific provider
)

# LLM Chat with automatic fallback  
result = await orchestrator.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    preferred_provider=None  # Uses config preference + fallback
)

# Translation
result = await orchestrator.translate_text(
    text="Hello",
    target_language="hi"
)

# Text-to-Speech
result = await orchestrator.text_to_speech(
    text="Hello world",
    voice="alloy"
)
```

**Key features:**
- ✅ Automatic provider selection based on configuration
- ✅ Fallback chain execution if primary provider fails  
- ✅ Comprehensive error handling and logging
- ✅ Performance timing for all operations
- ✅ Provider metadata in all results

---

### 5. Unified AI API (`interfaces/unified_ai_api.py`)

**Cloud-agnostic REST API** replacing provider-specific routes:

#### **New Unified Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/chat` | POST | LLM chat completion (Azure/Together/OpenAI) |
| `/api/ai/transcribe` | POST | Speech-to-Text (Azure/OpenAI) |
| `/api/ai/translate` | POST | Text translation (Azure) |
| `/api/ai/speak` | POST | Text-to-Speech (OpenAI/Azure) |
| `/api/ai/status` | GET | Provider status & configuration |
| `/api/ai/providers` | GET | List available providers |

#### **Example: Chat Completion**

```bash
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7,
    "provider": "azure"  # Optional: "together", "openai", or null for auto
  }'

Response:
{
  "content": "Hello! How can I help you today?",
  "model": "gpt-4.1-mini",
  "provider": "azure",
  "usage": {"total_tokens": 25},
  "duration_ms": 1200
}
```

#### **Example: Speech-to-Text**

```bash
curl -X POST http://localhost:8000/api/ai/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "<base64_audio_data>",
    "audio_format": "wav",
    "language": "en",
    "provider": null  # Auto-select
  }'

Response:
{
  "text": "Hello, this is a test.",
  "detected_language": "en",
  "confidence": 0.98,
  "method": "azure_speech",
  "provider": "azure",
  "duration_ms": 800
}
```

---

## Configuration

### Environment Variables

Control provider selection through `.env`:

```bash
# Primary LLM provider selection
LLM_PROVIDER=azure          # Options: azure, together, openai, auto
CHAT_PROVIDER=azure         # For chat completions
EMBEDDING_PROVIDER=azure    # For embeddings
BEAUTIFY_PROVIDER=azure     # For response beautification

# Voice services
VOICE_STT_PROVIDER=azure    # Speech-to-Text: azure, openai, auto
VOICE_TTS_PROVIDER=openai   # Text-to-Speech: openai, azure, auto

# Azure credentials
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://...
AZURE_SPEECH_KEY=your_key
AZURE_SPEECH_REGION=eastus2
AZURE_TRANSLATION_KEY=your_key
AZURE_TRANSLATION_REGION=eastus2

# Together AI credentials
TOGETHER_API_KEY=your_key
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo

# OpenAI credentials
OPENAI_API_KEY=your_key
OPENAI_WHISPER_MODEL=whisper-1
OPENAI_TTS_MODEL=tts-1
OPENAI_TTS_VOICE=alloy
```

### Provider Preferences

```python
# In shared/config.py
chat_provider: Optional[str] = "azure"       # For chat/conversation
embedding_provider: Optional[str] = "azure"  # For embeddings
beautify_provider: Optional[str] = "azure"   # For response beautification
```

---

## Provider Switching

### 1. **Via Configuration** (Recommended)

Change `.env` file:

```bash
# Switch from Azure to Together AI
LLM_PROVIDER=together
CHAT_PROVIDER=together
```

Restart application - all workflows now use Together AI!

### 2. **Via API Request** (Runtime)

Override provider per request:

```bash
# Use Together AI for this chat only
curl -X POST /api/ai/chat -d '{
  "messages": [...],
  "provider": "together"
}'

# Use Azure for this chat only
curl -X POST /api/ai/chat -d '{
  "messages": [...],
  "provider": "azure"
}'
```

### 3. **Automatic Fallback** (Default)

If primary provider fails, automatically tries fallback:

```
Azure fails → Together AI → OpenAI
```

```python
# Example orchestration logs:
🎙️  STT Request - Provider chain: ['azure', 'openai']
   Trying provider: azure
   ❌ azure failed: Connection timeout
   Trying provider: openai
   ✅ STT successful with openai (850ms)
```

---

## Comparison: Old vs New Architecture

### **Old Architecture** (Provider-Specific Routes)

```
❌ Direct routes to Azure services
❌ Tightly coupled to Azure APIs
❌ No fallback support
❌ Hard to switch providers
❌ Duplicate code for each provider

/api/azure/speech-to-text → Azure Speech Service
/api/azure/translate → Azure Translator
/api/azure/chat → Azure OpenAI
```

### **New Architecture** (Orchestration Layer)

```
✅ Unified cloud-agnostic interface
✅ Template-based provider implementations
✅ Automatic fallback chains
✅ Easy provider switching (config-driven)
✅ Modular, scalable design

/api/ai/transcribe → Orchestrator → [Azure | OpenAI]
/api/ai/translate → Orchestrator → [Azure]
/api/ai/chat → Orchestrator → [Azure | Together | OpenAI]
```

---

## Adding New Providers

### Step 1: Create Provider Implementation

```python
# orchestration/cloud_providers/implementations/anthropic_provider.py

from ..templates.base import CloudProvider, LLMProvider, LLMResult

class AnthropicProvider(CloudProvider, LLMProvider):
    def __init__(self, config: ProviderConfig, capability: ProviderCapability):
        super().__init__(config)
        self.capability = capability
        self._capabilities = [ProviderCapability.LLM_CHAT]
    
    def is_available(self) -> bool:
        return bool(self.config.api_key)
    
    async def chat_completion(self, messages, temperature, max_tokens, stream):
        # Implement using Anthropic SDK
        pass
    
    @property
    def model_name(self) -> str:
        return self.config.model or "claude-3-opus"
```

### Step 2: Register Provider

```python
# orchestration/cloud_providers/registry.py

from .implementations.anthropic_provider import AnthropicProvider

ProviderFactory.register_provider("anthropic", AnthropicProvider)
```

### Step 3: Add Configuration

```python
# shared/config.py

anthropic_api_key: Optional[str] = None
anthropic_model: Optional[str] = "claude-3-opus"
```

### Step 4: Update Fallback Chain

```python
# orchestration/cloud_providers/factory.py

def get_fallback_chain(capability: ProviderCapability) -> List[str]:
    if capability == ProviderCapability.LLM_CHAT:
        return ["azure", "together", "anthropic", "openai"]  # Added Anthropic
```

**That's it!** The orchestrator now supports Anthropic with zero changes to application code.

---

## Migration Path

### Phase 1: ✅ **Completed** - New Architecture Created
- ✅ Provider templates defined
- ✅ Azure, Together AI, OpenAI providers implemented
- ✅ Orchestration manager created
- ✅ Unified API endpoints created
- ✅ Factory pattern with auto-detection

### Phase 2: **In Progress** - Coexistence
- 🔄 Both `/api/azure/*` and `/api/ai/*` endpoints available
- 🔄 Old routes still work (backward compatible)
- 🔄 New routes use orchestration layer

### Phase 3: **Planned** - Migration
- ⏳ Migrate existing workflows to use `/api/ai/*` endpoints
- ⏳ Update frontend to use new unified endpoints
- ⏳ Test all scenarios with different providers

### Phase 4: **Planned** - Cleanup
- ⏳ Remove `/api/azure/*` routes
- ⏳ Clean up direct Azure service calls
- ⏳ Update documentation

---

## Benefits

### **For Users**
- 🎯 **Easy provider switching**: Change one ENV variable to switch providers
- 🎯 **Better reliability**: Automatic fallback if one provider fails
- 🎯 **Cost optimization**: Use cheaper providers for specific workflows
- 🎯 **Avoid vendor lock-in**: Not tied to single cloud provider

### **For Developers**
- 🔧 **Modular code**: Clean separation of concerns
- 🔧 **Easy testing**: Mock providers easily
- 🔧 **Scalable**: Add new providers without touching existing code
- 🔧 **Maintainable**: Standard interfaces reduce complexity

---

## Next Steps

1. **Test unified endpoints** with different provider configurations
2. **Update frontend** to use `/api/ai/*` endpoints
3. **Migrate workflows** from Azure-specific to orchestrated
4. **Add provider health monitoring** dashboard
5. **Implement caching** for expensive operations
6. **Add rate limiting** per provider

---

## Related Documentation

- **Azure AI Integration**: `AZURE_AI_INTEGRATION.md`
- **Vector DB Usage**: `VECTOR_DB_USAGE.md`
- **Project Overview**: `replit.md`

---

**Last Updated**: October 22, 2025  
**Version**: 1.0.0  
**Status**: Phase 2 (Coexistence)
