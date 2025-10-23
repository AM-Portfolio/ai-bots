# Azure AI Services Integration Guide

Complete integration guide for Azure AI Services with both **Service Endpoints** and **Model Deployments**.

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Available Services](#available-services)
5. [API Endpoints](#api-endpoints)
6. [Usage Examples](#usage-examples)
7. [Testing](#testing)

---

## Overview

This project integrates **both** Azure AI approaches for maximum flexibility:

### Service Endpoints
- ✅ **Azure Speech** - Speech-to-Text with language detection
- ✅ **Azure Translation** - Multi-language translation
- ✅ **Azure Language** - Text analysis and NLP

### Model Deployments
- ✅ **gpt-4o-transcribe-diarize** - Enhanced transcription with speaker identification
- ✅ **model-router** - Intelligent routing to GPT models
- ✅ **gpt-audio-mini** - Lightweight audio processing

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure AI Manager                          │
│  (Coordinates Service Endpoints + Model Deployments)        │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
┌─────────▼──────────┐        ┌──────────▼───────────┐
│ Service Endpoints  │        │ Model Deployments    │
│  - Speech STT      │        │  - GPT-4o Transcribe │
│  - Translation     │        │  - Model Router      │
│  - Language        │        │  - GPT Audio Mini    │
└────────────────────┘        └──────────────────────┘
```

### Separation of Concerns

```
API Layer           → interfaces/azure_test_api.py
Service Layer       → shared/azure_services/*_service.py
Orchestration Layer → shared/azure_services/azure_ai_manager.py
Business Logic      → Features that use Azure services
```

---

## Configuration

Add these environment variables to your `.env` file:

```bash
# ============================================================================
# Azure Speech Service (Service Endpoint)
# ============================================================================
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=eastus2

# ============================================================================
# Azure Translation Service (Service Endpoint)
# ============================================================================
AZURE_TRANSLATOR_KEY=your_azure_translator_key_here
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=eastus2

# ============================================================================
# Azure OpenAI Model Deployments
# ============================================================================
AZURE_OPENAI_ENDPOINT=https://munis-mgzdcoho-eastus2.openai.azure.com/
AZURE_OPENAI_KEY=your_azure_openai_key_here
AZURE_OPENAI_API_VERSION=2024-10-21

# Deployment Names (match your Azure AI Foundry deployments)
AZURE_GPT4O_TRANSCRIBE_DEPLOYMENT=gpt-4o-transcribe-diarize
AZURE_MODEL_ROUTER_DEPLOYMENT=model-router
AZURE_GPT_AUDIO_MINI_DEPLOYMENT=gpt-audio-mini

# ============================================================================
# Voice Assistant Configuration
# ============================================================================
VOICE_STT_PROVIDER=azure  # Use 'azure' for Azure Speech, 'openai' for Whisper
VOICE_TTS_PROVIDER=openai
```

### How to Get Azure Credentials

1. **Azure Portal**: Go to [portal.azure.com](https://portal.azure.com/)
2. **Create Resources**:
   - Cognitive Services (for Speech, Translation)
   - Azure OpenAI (for Model Deployments)
3. **Get Keys**: Navigate to "Keys and Endpoint" in each resource
4. **Copy Values**: Add KEY 1 and ENDPOINT to `.env`

---

## Available Services

### 1. Azure Speech Service
**File**: `shared/azure_services/speech_service.py`

```python
from shared.azure_services import AzureSpeechService

speech = AzureSpeechService()

# Transcribe audio with language detection
text, language = await speech.transcribe_audio(audio_base64, "webm")
```

### 2. Azure Translation Service
**File**: `shared/azure_services/translation_service.py`

```python
from shared.azure_services import AzureTranslationService

translator = AzureTranslationService()

# Translate to English
english_text, detected_lang = await translator.translate_to_english("Hola mundo")

# Translate to any language
translated, detected_lang = await translator.translate("Hello", target_language="es")

# Detect language only
language, confidence = await translator.detect_language("Bonjour")
```

### 3. Azure Model Deployment Service
**File**: `shared/azure_services/model_deployment_service.py`

```python
from shared.azure_services import AzureModelDeploymentService

models = AzureModelDeploymentService()

# Enhanced transcription with diarization
result = await models.transcribe_with_diarization("meeting.mp3")
# Returns: { text, language, duration, segments, speakers }

# Chat with model router
response = await models.chat_with_model_router([
    {"role": "user", "content": "Explain quantum computing"}
])

# Lightweight audio processing
text = await models.process_audio_mini("audio.wav", task="transcribe")
```

### 4. Azure AI Manager (Unified Orchestrator)
**File**: `shared/azure_services/azure_ai_manager.py`

```python
from shared.azure_services import AzureAIManager

manager = AzureAIManager()

# Voice assistant flow (STT → Translation → Ready for chat)
result = await manager.voice_assistant_flow(
    audio_base64=audio_data,
    audio_format="webm",
    use_enhanced_transcription=True
)

# Meeting transcription with diarization
transcript = await manager.meeting_transcription_flow("meeting.mp3")

# Multilingual chat
result = await manager.multilingual_chat_flow(
    user_message="Comment ça va?",
    target_language="fr"
)
```

---

## API Endpoints

All endpoints are available under `/api/azure/`:

### Service Status

#### `GET /api/azure/status`
Get status of all Azure AI services

**Response:**
```json
{
  "service_endpoints": {
    "speech": {
      "available": true,
      "endpoint": "eastus2.stt.speech.microsoft.com"
    },
    "translation": {
      "available": true,
      "endpoint": "https://api.cognitive.microsofttranslator.com"
    }
  },
  "model_deployments": {
    "available": true,
    "endpoint": "https://munis-mgzdcoho-eastus2.openai.azure.com/",
    "deployments": {
      "gpt4o_transcribe": {...},
      "model_router": {...},
      "gpt_audio_mini": {...}
    }
  }
}
```

#### `GET /api/azure/test-all`
Test all Azure AI services and workflows

#### `GET /api/azure/workflows`
Get list of available workflows based on configured services

#### `GET /api/azure/deployments`
Get detailed information about Model Deployments

---

### Voice Assistant Workflow

#### `POST /api/azure/voice-assistant`
Complete voice assistant flow: STT → Translation → Ready for orchestration

**Request:**
```json
{
  "audio_base64": "base64_encoded_audio_data",
  "audio_format": "webm",
  "use_enhanced_transcription": false
}
```

**Response:**
```json
{
  "original_text": "नमस्ते, आप कैसे हैं?",
  "translated_text": "Hello, how are you?",
  "detected_language": "hi",
  "needs_translation": true,
  "transcription_method": "azure_speech"
}
```

**Use Case**: Voice assistant, real-time speech interaction

---

### Meeting Transcription Workflow

#### `POST /api/azure/meeting-transcription`
Transcribe meeting with speaker diarization

**Request:** Upload audio file (multipart/form-data)

**Response:**
```json
{
  "text": "Full meeting transcript...",
  "language": "en",
  "duration": 3600.5,
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "Welcome to the meeting",
      "speaker": "speaker_1"
    },
    {
      "id": 1,
      "start": 5.5,
      "end": 10.8,
      "text": "Thank you for having me",
      "speaker": "speaker_2"
    }
  ],
  "speakers": ["speaker_1", "speaker_2"]
}
```

**Use Case**: Meeting summaries, podcast transcription, multi-speaker analysis

---

### Multilingual Chat Workflow

#### `POST /api/azure/multilingual-chat`
Chat in any language with automatic translation

**Request:**
```json
{
  "message": "¿Qué es la inteligencia artificial?",
  "source_language": null,
  "target_language": "es"
}
```

**Response:**
```json
{
  "original_message": "¿Qué es la inteligencia artificial?",
  "english_message": "What is artificial intelligence?",
  "detected_language": "es",
  "english_response": "Artificial intelligence is...",
  "translated_response": "La inteligencia artificial es...",
  "response_language": "es"
}
```

**Use Case**: Multilingual customer support, global chatbots

---

## Usage Examples

### Example 1: Voice Assistant with Translation

```python
import requests

# Record audio and convert to base64
audio_base64 = get_audio_from_mic()

# Process with Azure
response = requests.post("http://localhost:8000/api/azure/voice-assistant", json={
    "audio_base64": audio_base64,
    "audio_format": "webm",
    "use_enhanced_transcription": False  # Use Azure Speech (faster)
})

result = response.json()
print(f"You said ({result['detected_language']}): {result['original_text']}")
print(f"Translated: {result['translated_text']}")

# Now send to backend orchestration
# ... process with LLM, commit workflow, etc.
```

### Example 2: Meeting Transcription with Diarization

```python
# Upload meeting recording
with open("team_meeting.mp3", "rb") as audio_file:
    response = requests.post(
        "http://localhost:8000/api/azure/meeting-transcription",
        files={"audio_file": audio_file}
    )

transcript = response.json()

# Print speaker-separated transcript
for segment in transcript["segments"]:
    speaker = segment["speaker"]
    text = segment["text"]
    start = segment["start"]
    print(f"[{start:.1f}s] {speaker}: {text}")

# Summary
print(f"\nMeeting Duration: {transcript['duration']}s")
print(f"Total Speakers: {len(transcript['speakers'])}")
```

### Example 3: Multilingual Customer Support

```python
# Customer message in any language
customer_message = "Mi pedido no ha llegado"

response = requests.post("http://localhost:8000/api/azure/multilingual-chat", json={
    "message": customer_message,
    "target_language": "es"  # Respond in Spanish
})

result = response.json()

# System processes in English internally
print(f"Internal (English): {result['english_message']}")
print(f"AI Response (English): {result['english_response']}")

# Customer sees response in their language
print(f"\nTo Customer (Spanish): {result['translated_response']}")
```

---

## Testing

### Test All Services

```bash
curl http://localhost:8000/api/azure/test-all
```

### Test Individual Services

```bash
# Translation only
curl -X POST http://localhost:8000/api/translation/translate-to-english \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour le monde"}'

# Get available workflows
curl http://localhost:8000/api/azure/workflows

# Check service status
curl http://localhost:8000/api/azure/status
```

### Integration Test with Frontend

1. Open Voice Assistant tab
2. Click microphone (speaks in Hindi/Spanish/etc.)
3. System automatically:
   - Transcribes with Azure Speech
   - Translates to English
   - Processes with backend
   - Responds with TTS

---

## Workflow Recommendations

Based on your use case, choose the right service:

| Your Goal | Best Choice | Why |
|-----------|-------------|-----|
| **Voice assistant / live speech** | ✅ Azure Speech (Service Endpoint) | Real-time streaming, cheaper for continuous audio |
| **Meeting transcription / podcasts** | ✅ GPT-4o Transcribe (Model Deployment) | Speaker diarization + better accuracy |
| **General chatbot with reasoning** | ✅ Model Router (Model Deployment) | Intelligent routing to best GPT model |
| **Simple language translation** | ✅ Azure Translator (Service Endpoint) | Fast, cheap, 100+ languages |
| **Multimodal AI agent** | ✅ Combine Both | Use Service Endpoints + Model Deployments |

---

## Next Steps

1. **Add Azure credentials** to `.env` file
2. **Test endpoints** with `/api/azure/test-all`
3. **Integrate with Voice Assistant** - Already configured!
4. **Try multilingual chat** in LLM Testing page
5. **Upload meeting recordings** for transcription

All services have **graceful fallbacks** - they work without Azure credentials (with warnings).

---

## Support

For issues or questions:
- Check logs: `/tmp/logs/AI_Dev_Agent_*.log`
- API docs: `http://localhost:8000/docs` (FastAPI auto-generated)
- Azure Portal: [portal.azure.com](https://portal.azure.com/)
