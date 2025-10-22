# AI-Bots Architecture Diagrams

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph "User Interface"
        A[User Input: Voice or Text]
    end
    
    subgraph "Input Processing Layer"
        B{Input Router}
        D[Azure Speech-to-Text]
    end
    
    subgraph "Intent & Logic Layer"
        C[Text Processing]
        E{Intent Classifier}
    end
    
    subgraph "Backend Services"
        F[Qdrant Vector DB<br/>+ Code AI]
        G[Azure OpenAI<br/>GPT-4.1 Mini]
    end
    
    subgraph "Response Generation"
        H[Response Text Generator]
        I[Azure Text-to-Speech]
    end
    
    subgraph "Output"
        J[User Output:<br/>Text + Audio]
    end
    
    A -->|Voice| B
    A -->|Text| B
    B -->|Voice| D
    B -->|Text| C
    D --> C
    C --> E
    E -->|Repo-related| F
    E -->|General| G
    F --> H
    G --> H
    H --> I
    I --> J
```

---

## 2. LLM Provider Architecture (After Migration)

```mermaid
graph LR
    subgraph "LLM Request"
        A[Application Request]
    end
    
    subgraph "Provider Selection"
        B{LLM Factory}
        C[Config:<br/>LLM_PROVIDER=azure]
    end
    
    subgraph "Primary Provider"
        D[Azure OpenAI<br/>GPT-4.1 Mini]
        D1[Available?]
    end
    
    subgraph "Fallback Provider"
        E[Together AI<br/>Llama 3.3 70B]
        E1[Available?]
    end
    
    subgraph "Response"
        F[LLM Response]
    end
    
    A --> B
    C --> B
    B --> D
    D --> D1
    D1 -->|Yes| F
    D1 -->|No| E
    E --> E1
    E1 -->|Yes| F
    E1 -->|No| F
```

---

## 3. Input Routing Flow

```mermaid
sequenceDiagram
    participant User
    participant InputRouter
    participant AzureSpeech
    participant IntentClassifier
    participant QdrantBackend
    participant AzureAI
    participant ResponseGen
    
    User->>InputRouter: Input (voice/text)
    
    alt Voice Input
        InputRouter->>AzureSpeech: Transcribe audio
        AzureSpeech-->>InputRouter: Text + Language
    else Text Input
        Note over InputRouter: Direct text processing
    end
    
    InputRouter->>IntentClassifier: Classify intent
    
    alt Repo-related
        IntentClassifier->>QdrantBackend: Query code context
        QdrantBackend-->>ResponseGen: Code snippets
    else General
        IntentClassifier->>AzureAI: Process query
        AzureAI-->>ResponseGen: Response
    end
    
    ResponseGen->>AzureSpeech: Generate audio (optional)
    AzureSpeech-->>User: Text + Audio response
```

---

## 4. Provider Fallback Mechanism

```mermaid
graph TD
    A[LLM Request] --> B{Primary Provider<br/>Azure OpenAI}
    B -->|Success| C[Return Response]
    B -->|Failure| D{Fallback Provider<br/>Together AI}
    D -->|Success| C
    D -->|Failure| E[Error Response]
    
    style B fill:#0078d4,color:#fff
    style D fill:#ff6b6b,color:#fff
    style C fill:#51cf66,color:#fff
    style E fill:#fa5252,color:#fff
```

---

## 5. Intent Classification Logic

```mermaid
graph TD
    A[User Query] --> B{Extract Keywords}
    B --> C[Repo Keywords Found?]
    B --> D[Code References Found?]
    B --> E[General Keywords Found?]
    
    C -->|Yes| F[+0.15 per keyword]
    D -->|Yes| G[+0.30 per reference]
    E -->|Yes| H[-0.20 penalty]
    
    F --> I{Calculate Score}
    G --> I
    H --> I
    
    I -->|Score > 0.3| J[REPO-RELATED]
    I -->|Score ≤ 0.3| K[GENERAL]
    
    J --> L[Route to Qdrant]
    K --> M[Route to Azure AI]
    
    style J fill:#51cf66,color:#fff
    style K fill:#339af0,color:#fff
```

---

## 6. Voice-to-Voice Pipeline

```mermaid
graph LR
    A[🎤 Voice Input] --> B[Input Router]
    B --> C[Azure Speech-to-Text]
    C --> D[Text Transcription]
    D --> E[Intent Classifier]
    
    E -->|Repo| F[Qdrant Backend]
    E -->|General| G[Azure OpenAI]
    
    F --> H[Response Generator]
    G --> H
    
    H --> I[Azure Text-to-Speech]
    I --> J[🔊 Voice Output]
    
    style C fill:#0078d4,color:#fff
    style I fill:#0078d4,color:#fff
```

---

## 7. Module Dependencies

```mermaid
graph TD
    subgraph "Frontend"
        UI[ui/app.py]
    end
    
    subgraph "API Layer"
        API[interfaces/http_api/]
    end
    
    subgraph "Orchestration"
        ORCH[orchestration/facade.py]
        ROUTER[shared/routing/input_router.py]
        INTENT[shared/routing/intent_classifier.py]
    end
    
    subgraph "Shared Services"
        LLM[shared/llm.py]
        SPEECH[shared/azure_services/speech_service.py]
        EMBED[shared/vector_db/embedding_service.py]
    end
    
    subgraph "LLM Providers"
        FACTORY[shared/llm_providers/factory.py]
        AZURE[shared/llm_providers/azure_provider.py]
        TOGETHER[shared/llm_providers/together_provider.py]
    end
    
    subgraph "Backend"
        QDRANT[vector_db/]
        DB[db/]
    end
    
    UI --> API
    API --> ORCH
    ORCH --> ROUTER
    ORCH --> INTENT
    ORCH --> LLM
    
    ROUTER --> SPEECH
    
    LLM --> FACTORY
    FACTORY --> AZURE
    FACTORY --> TOGETHER
    
    ORCH --> EMBED
    ORCH --> QDRANT
    ORCH --> DB
    
    EMBED --> FACTORY
```

---

## 8. Configuration Hierarchy

```mermaid
graph TD
    A[.env File] --> B[shared/config.py<br/>Settings]
    B --> C[LLM Provider Config]
    B --> D[Azure Services Config]
    B --> E[Vector DB Config]
    
    C --> F[shared/llm_providers/factory.py]
    D --> G[shared/azure_services/]
    E --> H[shared/vector_db/]
    
    F --> I[Azure OpenAI Provider]
    F --> J[Together AI Provider]
    
    G --> K[Speech Service]
    G --> L[Translation Service]
    
    H --> M[Qdrant Provider]
    H --> N[Embedding Service]
    
    style A fill:#ffd43b,color:#000
    style I fill:#0078d4,color:#fff
    style J fill:#ff6b6b,color:#fff
```

---

## 9. Data Flow: Voice Query to Audio Response

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Frontend UI
    participant API as HTTP API
    participant Router as Input Router
    participant STT as Azure STT
    participant Intent as Intent Classifier
    participant Backend as Qdrant/Azure AI
    participant LLM as Azure OpenAI
    participant TTS as Azure TTS
    
    User->>UI: 🎤 Voice Recording
    UI->>API: POST /api/v1/input/voice
    API->>Router: Route input
    Router->>STT: Transcribe audio
    STT-->>Router: Text + Language
    
    Router->>Intent: Classify intent
    Intent-->>Router: is_repo_related=true
    
    alt Repo-related
        Router->>Backend: Query Qdrant
        Backend-->>LLM: Code context
    else General
        Router->>LLM: Direct query
    end
    
    LLM-->>API: Response text
    API->>TTS: Synthesize speech
    TTS-->>API: Audio data
    API-->>UI: Text + Audio
    UI-->>User: 🔊 Play audio + Display text
```

---

## 10. Error Handling & Fallback Flow

```mermaid
graph TD
    A[Request] --> B{Azure OpenAI}
    B -->|Success| C[✅ Return Response]
    B -->|Timeout| D{Retry Logic}
    B -->|Auth Error| E{Check Config}
    B -->|Rate Limit| F{Wait & Retry}
    B -->|Other Error| G{Fallback to Together AI}
    
    D -->|Retry| B
    D -->|Max Retries| G
    
    E -->|Invalid| H[❌ Config Error]
    E -->|Valid| B
    
    F -->|Wait| B
    F -->|Max Wait| G
    
    G -->|Success| C
    G -->|Failure| I[❌ All Providers Failed]
    
    style C fill:#51cf66,color:#fff
    style H fill:#fa5252,color:#fff
    style I fill:#fa5252,color:#fff
```

---

## Key Architecture Decisions

### 1. **Azure as Default Provider**
- Primary: Azure OpenAI (Enterprise-grade, compliance)
- Fallback: Together AI (Cost-effective, fast)

### 2. **Layered Architecture**
- Frontend → API → Orchestration → Services → Providers
- Clear separation of concerns
- Easy to test and maintain

### 3. **Intent-Based Routing**
- Repo-related queries → Qdrant + Code AI
- General queries → Azure OpenAI
- Automatic classification based on keywords/patterns

### 4. **Voice-First Design**
- Azure Speech-to-Text for input
- Azure Text-to-Speech for output
- Support for multiple languages

### 5. **Flexible Configuration**
- Environment-based settings
- Role-based provider assignment
- Easy to switch providers

---

## Performance Targets

| Component | Target Latency |
|-----------|----------------|
| Speech-to-Text | < 2 seconds |
| Intent Classification | < 100ms |
| Azure OpenAI LLM | < 3 seconds |
| Text-to-Speech | < 3 seconds |
| **Total (Voice-to-Voice)** | **< 10 seconds** |

---

**Generated**: October 22, 2025  
**Version**: 1.0
