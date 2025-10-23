# Azure Migration Plan: Making Azure the Default Provider

## Current State Analysis

### 🔍 **Current Implementation**
The `ai-bots` repository currently uses **Together AI as the default LLM provider** with Azure OpenAI as a fallback option.

**Key Components Using Together AI**:
1. **LLM Chat Completion** (`shared/llm.py`, `shared/llm_providers/together_provider.py`)
   - Default model: `meta-llama/Llama-3.3-70B-Instruct-Turbo`
   - Used for code analysis, test generation, documentation
   
2. **Embeddings** (`shared/vector_db/embedding_service.py`)
   - Default model: `togethercomputer/m2-bert-80M-32k-retrieval`
   - Used for Qdrant vector search
   
3. **Configuration** (`shared/config.py`)
   - `llm_provider`: Currently defaults to "together"
   - Environment variable: `LLM_PROVIDER` (set to "azure" in `.env`)

### 🎯 **Migration Goal**
Switch to **Azure as the default provider** across all components while maintaining Together AI as an optional fallback.

---

## Migration Strategy

### **Phase 1: Configuration Updates** ✅ (Already Partially Done)

#### 1.1 Environment Variables
**Status**: `.env` already has `LLM_PROVIDER=azure` 

**Current Azure Resources Available**:
- ✅ Azure OpenAI Endpoint: `https://munis-mgzdcoho-eastus2.cognitiveservices.azure.com/`
- ✅ Azure OpenAI Deployment: `gpt-4.1-mini`
- ✅ Azure Speech Services (STT/TTS): `eastus2`
- ✅ Azure Translation Service
- ✅ Azure AI Services Multi-service endpoint
- ✅ Azure Embedding Deployment: `text-embedding-ada-002`
- ✅ Azure Model Deployments: `gpt-4o-transcribe-diarize`, `model-router`, `gpt-audio-mini`

**Action Items**:
- [x] ~~Set `LLM_PROVIDER=azure` in `.env`~~ (Already done)
- [ ] Set `EMBEDDING_PROVIDER=azure` in `.env` (needs to be added)
- [ ] Update default provider in `shared/config.py` to "azure"
- [ ] Document Together AI as optional fallback

---

### **Phase 2: Code Updates**

#### 2.1 Update LLM Factory Defaults
**File**: `shared/llm_providers/factory.py`

**Changes**:
```python
# Change default from "together" to "azure"
def get_llm_client(
    provider_type: str = "azure",  # Changed from "together"
    azure_endpoint: Optional[str] = None,
    azure_api_key: Optional[str] = None,
    azure_deployment: str = "gpt-4.1-mini",  # Updated default
    azure_api_version: str = "2025-04-14",  # Updated API version
    together_api_key: Optional[str] = None,
    together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
) -> BaseLLMProvider:
```

**Fallback Logic**:
```python
# If Azure fails, fallback to Together AI
if provider_type == "azure" and not client.is_available():
    if together_api_key:
        logger.info("Azure not available, falling back to Together AI")
        fallback_client = TogetherAIProvider(
            api_key=together_api_key,
            model=together_model
        )
        if fallback_client.is_available():
            return fallback_client
```

---

#### 2.2 Update Embedding Service
**File**: `shared/vector_db/embedding_service.py`

**Current Default**: Together AI (`togethercomputer/m2-bert-80M-32k-retrieval`)

**Changes**:
1. Change default provider initialization:
```python
def __init__(
    self,
    provider: str = "auto",  # Keep auto-detection
    api_key: Optional[str] = None,
    embedding_model: Optional[str] = None
):
    # Determine provider priority: Azure > Together > Fallback
    if provider == "auto":
        if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
            self.provider = "azure"
        elif os.getenv("TOGETHER_API_KEY"):
            self.provider = "together"
        else:
            self.provider = "fallback"
    else:
        self.provider = provider
```

2. Update model selection:
```python
if self.provider == "azure":
    self.embedding_model = "text-embedding-ada-002"  # Azure default
    self._initialize_azure_client()
elif self.provider == "together":
    self.embedding_model = "togethercomputer/m2-bert-80M-32k-retrieval"
    self._initialize_together_client()
```

3. Add Azure embedding client initialization:
```python
def _initialize_azure_client(self):
    """Initialize Azure OpenAI client for embeddings"""
    try:
        from openai import AzureOpenAI
        
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        
        if not endpoint or not api_key:
            logger.warning("⚠️  Azure OpenAI credentials not found, using fallback")
            self.client = None
            return
        
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version="2025-04-14",
            azure_endpoint=endpoint
        )
        
        logger.info("✅ Azure OpenAI embedding client initialized")
    except Exception as e:
        logger.warning(f"⚠️  Failed to initialize Azure OpenAI client: {e}")
        self.client = None
```

4. Update `generate_embedding` method:
```python
async def generate_embedding(self, text: str) -> List[float]:
    # Try Azure first
    if self.provider == "azure" and self.client:
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Azure embedding failed: {e}, trying fallback")
    
    # Try Together AI
    if self.provider == "together" and self.client:
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Together AI embedding failed: {e}, using hash fallback")
    
    # Hash fallback
    return self._generate_fallback_embedding(text)
```

---

#### 2.3 Update Configuration Defaults
**File**: `shared/config.py`

**Changes**:
```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # Primary LLM Provider (azure or together)
    llm_provider: Optional[str] = "azure"  # Changed default from None to "azure"
    
    # Azure OpenAI Configuration (set defaults)
    azure_openai_deployment_name: Optional[str] = "gpt-4.1-mini"  # Set default
    azure_openai_api_version: Optional[str] = "2025-04-14"  # Set default
    azure_openai_embedding_deployment: Optional[str] = "text-embedding-ada-002"  # Set default
    
    # Role-Based Provider Assignment
    chat_provider: Optional[str] = "azure"           # Changed default
    embedding_provider: Optional[str] = "azure"      # Changed default
    beautify_provider: Optional[str] = "azure"       # Changed default
```

---

#### 2.4 Update Main Application
**File**: `main.py`

**Changes**:
```python
def display_configuration():
    """Display current configuration"""
    logger.info("Configuration:")
    logger.info(f"   • LLM Provider: {settings.llm_provider}")
    
    # Show Azure config first (now default)
    if settings.llm_provider == "azure":
        logger.info(f"   • Azure Endpoint: {settings.azure_openai_endpoint}")
        logger.info(f"   • Azure Deployment: {settings.azure_openai_deployment_name}")
        logger.info(f"   • Azure API Version: {settings.azure_openai_api_version}")
        logger.info(f"   • Azure API Key: {'✓ Configured' if settings.azure_openai_api_key else '✗ Missing'}")
        logger.info(f"   • Fallback to Together AI: {'✓ Available' if settings.together_api_key else '✗ Not configured'}")
    else:
        logger.info(f"   • Together Model: {settings.together_model}")
        logger.info(f"   • Together API Key: {'✓ Configured' if settings.together_api_key else '✗ Missing'}")
        logger.info(f"   • Fallback to Azure: {'✓ Available' if settings.azure_openai_api_key else '✗ Not configured'}")

def validate_configuration():
    """Validate required configuration"""
    missing = []
    
    if settings.llm_provider == "azure":
        if not settings.azure_openai_endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not settings.azure_openai_api_key:
            missing.append("AZURE_OPENAI_API_KEY")
        if not settings.azure_openai_deployment_name:
            missing.append("AZURE_OPENAI_DEPLOYMENT_NAME")
    elif settings.llm_provider == "together":
        if not settings.together_api_key:
            missing.append("TOGETHER_API_KEY")
    
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        return False
    
    return True
```

---

#### 2.5 Update UI Components
**File**: `ui/app.py`

**Changes**:
```python
# Update provider selection to default to Azure
provider = st.selectbox(
    "Provider", 
    ["azure", "together"],  # Changed order: Azure first
    index=0,  # Azure is default
    label_visibility="collapsed"
)

# Update display text
if provider == "azure":
    st.write("- **Model:** Azure OpenAI GPT-4.1 Mini")
    st.write("- **API:** Azure Cognitive Services")
    st.write("- **Fallback:** Together AI (if configured)")
else:
    st.write("- **Model:** Llama 3.3 70B Instruct Turbo")
    st.write("- **API:** Together AI OpenAI-compatible")
    st.write("- **Fallback:** Azure OpenAI (if configured)")
```

**File**: `ui/api_client.py`

**Changes**:
```python
def test_llm(self, prompt: str, provider: str = "azure") -> Dict[str, Any]:
    # Changed default from "together" to "azure"
```

---

### **Phase 3: Azure Speech Integration**

#### 3.1 Speech-to-Text (STT)
**Location**: Create `shared/azure_services/speech_service.py`

**Implementation**:
```python
import azure.cognitiveservices.speech as speechsdk
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AzureSpeechService:
    """Azure Speech Service for STT and TTS"""
    
    def __init__(self):
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION", "eastus2")
        self.speech_lang = os.getenv("AZURE_SPEECH_LANG", "en-US")
        self.speech_config = None
        self._initialize_speech_config()
    
    def _initialize_speech_config(self):
        """Initialize Azure Speech configuration"""
        if not self.speech_key:
            logger.warning("Azure Speech key not configured")
            return
        
        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.speech_region
            )
            self.speech_config.speech_recognition_language = self.speech_lang
            logger.info(f"✅ Azure Speech Service initialized (Region: {self.speech_region})")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Speech: {e}")
            self.speech_config = None
    
    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file to text using Azure Speech-to-Text
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.speech_config:
            logger.error("Azure Speech not configured")
            return None
        
        try:
            audio_config = speechsdk.AudioConfig(filename=audio_file_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                logger.info(f"✅ Transcribed: {result.text[:100]}...")
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech could be recognized")
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Speech recognition canceled: {cancellation.reason}")
                return None
            
        except Exception as e:
            logger.error(f"Azure Speech transcription failed: {e}")
            return None
    
    async def synthesize_speech(
        self,
        text: str,
        output_file_path: str,
        voice_name: str = "en-US-AvaMultilingualNeural"
    ) -> bool:
        """
        Synthesize text to speech using Azure Text-to-Speech
        
        Args:
            text: Text to synthesize
            output_file_path: Path to save audio file
            voice_name: Azure Neural voice name
            
        Returns:
            True if successful, False otherwise
        """
        if not self.speech_config:
            logger.error("Azure Speech not configured")
            return False
        
        try:
            self.speech_config.speech_synthesis_voice_name = voice_name
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file_path)
            
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            result = speech_synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"✅ Speech synthesized to {output_file_path}")
                return True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Speech synthesis canceled: {cancellation.reason}")
                return False
            
        except Exception as e:
            logger.error(f"Azure Speech synthesis failed: {e}")
            return False

# Global instance
azure_speech_service = AzureSpeechService()
```

---

#### 3.2 Input Router
**Location**: Create `shared/routing/input_router.py`

**Implementation**:
```python
from typing import Dict, Any, Optional
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class InputType(Enum):
    TEXT = "text"
    VOICE = "voice"
    UNKNOWN = "unknown"

class InputRouter:
    """Routes user input (voice or text) to appropriate processing pipeline"""
    
    def __init__(self, speech_service):
        self.speech_service = speech_service
    
    async def route(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route input to appropriate processing pipeline
        
        Args:
            input_data: {
                "type": "text" or "voice",
                "content": text content or file path,
                "metadata": optional metadata
            }
            
        Returns:
            {
                "input_type": InputType,
                "text": processed text,
                "original": original input
            }
        """
        input_type = self._detect_input_type(input_data)
        
        if input_type == InputType.VOICE:
            # Transcribe voice to text using Azure Speech-to-Text
            audio_file = input_data.get("content")
            text = await self.speech_service.transcribe_audio(audio_file)
            
            if not text:
                logger.error("Failed to transcribe voice input")
                return {
                    "input_type": InputType.UNKNOWN,
                    "text": None,
                    "original": input_data,
                    "error": "Transcription failed"
                }
            
            logger.info(f"✅ Voice input transcribed: {text[:100]}...")
            return {
                "input_type": InputType.VOICE,
                "text": text,
                "original": input_data
            }
        
        elif input_type == InputType.TEXT:
            # Direct text input
            text = input_data.get("content")
            logger.info(f"✅ Text input received: {text[:100]}...")
            return {
                "input_type": InputType.TEXT,
                "text": text,
                "original": input_data
            }
        
        else:
            logger.error("Unknown input type")
            return {
                "input_type": InputType.UNKNOWN,
                "text": None,
                "original": input_data,
                "error": "Unknown input type"
            }
    
    def _detect_input_type(self, input_data: Dict[str, Any]) -> InputType:
        """Detect input type from input data"""
        input_type_str = input_data.get("type", "").lower()
        
        if input_type_str == "voice":
            return InputType.VOICE
        elif input_type_str == "text":
            return InputType.TEXT
        else:
            return InputType.UNKNOWN
```

---

#### 3.3 Intent Classifier
**Location**: Create `shared/routing/intent_classifier.py`

**Implementation**:
```python
from typing import Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Classifies user intent as repo-related or general"""
    
    # Repo-related keywords
    REPO_KEYWORDS = [
        "code", "repo", "repository", "file", "function", "class",
        "bug", "issue", "pull request", "commit", "branch", "merge",
        "test", "deploy", "build", "ci/cd", "github", "git",
        "analyze", "refactor", "optimize", "debug", "fix",
        "documentation", "readme", "api", "endpoint", "database"
    ]
    
    # Reference patterns
    REFERENCE_PATTERNS = [
        r'#\d+',  # Issue/PR numbers
        r'[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+',  # repo/name
        r'[a-zA-Z0-9_-]+\.py',  # Python files
        r'[a-zA-Z0-9_-]+\.js',  # JavaScript files
        r'[a-zA-Z0-9_-]+\.[a-zA-Z]{2,4}',  # Other files
    ]
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify user intent
        
        Args:
            text: User input text
            
        Returns:
            {
                "is_repo_related": bool,
                "confidence": float,
                "matched_keywords": list,
                "matched_patterns": list
            }
        """
        text_lower = text.lower()
        
        # Check for repo keywords
        matched_keywords = [
            kw for kw in self.REPO_KEYWORDS
            if kw in text_lower
        ]
        
        # Check for reference patterns
        matched_patterns = []
        for pattern in self.REFERENCE_PATTERNS:
            if re.search(pattern, text):
                matched_patterns.append(pattern)
        
        # Calculate confidence
        keyword_score = min(len(matched_keywords) * 0.2, 0.7)
        pattern_score = min(len(matched_patterns) * 0.3, 0.3)
        confidence = keyword_score + pattern_score
        
        is_repo_related = confidence > 0.3
        
        logger.info(
            f"Intent classification: {'REPO' if is_repo_related else 'GENERAL'} "
            f"(confidence: {confidence:.2f})"
        )
        
        return {
            "is_repo_related": is_repo_related,
            "confidence": confidence,
            "matched_keywords": matched_keywords,
            "matched_patterns": matched_patterns
        }
```

---

### **Phase 4: Orchestration Updates**

#### 4.1 Main Orchestrator
**Location**: Update `orchestration/facade.py`

**Changes**:
```python
async def process_message(
    self,
    message: str,
    template_name: str = "default",
    execute_tasks: bool = True,
    input_type: str = "text",  # NEW: Add input type
    **kwargs
) -> Dict[str, Any]:
    """
    Process a user message through the entire pipeline
    
    Args:
        message: Raw user message (text or transcribed)
        template_name: Prompt template to use
        execute_tasks: Whether to execute planned tasks
        input_type: "text" or "voice"
        **kwargs: Additional parameters
        
    Returns:
        Complete processing result with all pipeline outputs
    """
    logger.info(
        "🚀 Starting orchestration pipeline",
        extra={
            "input_type": input_type,
            "message_length": len(message),
            "message_preview": message[:100],
            "template_name": template_name,
            "execute_tasks": execute_tasks,
            "llm_provider": settings.llm_provider  # Log current provider
        }
    )
    
    # ... rest of existing code ...
```

---

### **Phase 5: Testing Updates**

#### 5.1 Update Test Scripts
**Files to Update**:
- `test_embeddings.py`
- `test_embedding_config.py`
- `test_azure_config.py`

**Changes**:
```python
# test_embeddings.py
def main():
    print("🧪 Testing Embedding Service with Azure + Fallback")
    print("=" * 60)
    
    # Test with Azure first (new default)
    service = EmbeddingService(provider="auto")  # Will auto-detect Azure
    
    # ... rest of tests ...
    
    # Test provider availability
    print("\n6️⃣ Provider Availability:")
    print("-" * 60)
    if os.getenv("AZURE_OPENAI_API_KEY"):
        print("  🌐 Azure OpenAI API is available")
    else:
        print("  ⚠️  Azure OpenAI not configured")
    
    if os.getenv("TOGETHER_API_KEY"):
        print("  🌐 Together AI API is available (fallback)")
    else:
        print("  ⚠️  Together AI not configured")
```

---

### **Phase 6: Documentation Updates**

#### 6.1 Update README.md
Add Azure-first setup instructions:

```markdown
## Setup

### 1. Azure Configuration (Primary Provider)

Set the following environment variables in `.env`:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2025-04-14

# Azure Speech Services
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=eastus2

# Azure Embeddings
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### 2. Optional: Together AI (Fallback Provider)

For fallback capabilities, add:

```bash
TOGETHER_API_KEY=your-together-api-key
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
```

### 3. LLM Provider Configuration

Set your preferred provider:

```bash
LLM_PROVIDER=azure  # or "together"
```
```

---

## Implementation Checklist

### **Sprint 1: Core Provider Switch** (Week 1)
- [ ] Update `shared/config.py` defaults to Azure
- [ ] Update `shared/llm_providers/factory.py` default provider
- [ ] Update `shared/llm.py` initialization
- [ ] Update `.env` file with all Azure credentials
- [ ] Test LLM provider switch
- [ ] Verify fallback to Together AI works

### **Sprint 2: Embedding Migration** (Week 1-2)
- [ ] Add Azure embedding client to `embedding_service.py`
- [ ] Update embedding provider logic to prioritize Azure
- [ ] Test Azure embeddings with Qdrant
- [ ] Verify Together AI fallback for embeddings
- [ ] Performance testing: Azure vs Together embeddings

### **Sprint 3: Speech Integration** (Week 2)
- [ ] Create `shared/azure_services/speech_service.py`
- [ ] Implement Azure Speech-to-Text
- [ ] Implement Azure Text-to-Speech
- [ ] Add voice cloning configuration
- [ ] Test audio input/output pipeline

### **Sprint 4: Routing & Intent** (Week 2-3)
- [ ] Create `shared/routing/input_router.py`
- [ ] Create `shared/routing/intent_classifier.py`
- [ ] Integrate router with orchestration pipeline
- [ ] Test voice → text → logic → response → audio flow
- [ ] Test repo vs non-repo classification

### **Sprint 5: Testing & Validation** (Week 3)
- [ ] Update all test scripts
- [ ] Add Azure-specific unit tests
- [ ] Integration testing: Full pipeline
- [ ] Performance benchmarking
- [ ] Error handling and fallback testing

### **Sprint 6: Documentation & Cleanup** (Week 4)
- [ ] Update README.md
- [ ] Update INTEGRATION_PLAN.md
- [ ] Add Azure setup guide
- [ ] Update API documentation
- [ ] Remove deprecated Together AI references
- [ ] Final testing and deployment

---

## Migration Risks & Mitigation

### **Risk 1: Azure API Rate Limits**
- **Mitigation**: Implement retry logic with exponential backoff
- **Fallback**: Automatic failover to Together AI

### **Risk 2: Azure Embedding Model Compatibility**
- **Impact**: Vector DB queries may return different results
- **Mitigation**: 
  - Re-index Qdrant with Azure embeddings
  - Or maintain both embedding models with mapping

### **Risk 3: Cost Implications**
- **Azure**: Pay-per-use (could be higher cost)
- **Together**: Fixed pricing
- **Mitigation**: Monitor usage and set budget alerts

### **Risk 4: Performance Differences**
- **Together AI**: May be faster for some models
- **Azure**: Better for enterprise/compliance
- **Mitigation**: Benchmark both and use appropriate provider per task

---

## Rollback Plan

If Azure migration causes issues:

1. **Quick Rollback** (5 minutes):
   ```bash
   # In .env
   LLM_PROVIDER=together
   EMBEDDING_PROVIDER=together
   ```

2. **Code Rollback** (1 hour):
   - Revert `shared/config.py` defaults
   - Revert `factory.py` defaults
   - Keep Azure code for future use

3. **Full Rollback** (2 hours):
   - Remove Azure service integrations
   - Restore Together AI as primary
   - Update documentation

---

## Success Metrics

### **Performance**
- [ ] Chat completion latency < 3 seconds (Azure)
- [ ] Embedding generation < 1 second (Azure)
- [ ] Speech-to-Text < 2 seconds (Azure)
- [ ] Text-to-Speech < 3 seconds (Azure)

### **Reliability**
- [ ] Azure uptime > 99.9%
- [ ] Fallback activation < 1% of requests
- [ ] Zero data loss during migration

### **Cost**
- [ ] Azure costs within budget
- [ ] Cost per request tracked
- [ ] Usage alerts configured

---

## Timeline

| Week | Phase | Deliverable |
|------|-------|-------------|
| 1 | Core Switch + Embeddings | Azure as default LLM & embeddings |
| 2 | Speech Integration | Voice input/output working |
| 3 | Routing & Testing | Full pipeline tested |
| 4 | Documentation | Production-ready |

---

## Next Steps

1. **Review this plan** with team
2. **Set up Azure resources** (already done ✅)
3. **Begin Sprint 1** implementation
4. **Weekly check-ins** to track progress
5. **Performance monitoring** throughout migration

---

**Last Updated**: October 22, 2025  
**Status**: Ready for Implementation  
**Owner**: Development Team
