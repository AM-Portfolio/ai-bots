# Conversational Context Management

## Overview

The Conversational Context Manager enables intelligent multi-turn conversations in the LLM Testing UI by automatically maintaining and injecting context from previous messages. Users can mention a repository once, then ask follow-up questions without repeating the repository name or other contextual details.

## Features

### Smart Context Extraction
- **Repository Detection**: Automatically extracts repository names from conversation history
- **File Path Tracking**: Identifies and maintains file references across messages
- **Code Entity Detection**: Tracks functions, classes, and methods mentioned
- **Topic Recognition**: Identifies discussion topics (authentication, API, database, etc.)

### Intelligent Query Augmentation
- **Follow-up Detection**: Recognizes questions that reference previous context
- **Repository Context Injection**: Automatically prepends repository names to follow-up queries
- **Context Switching**: Detects topic changes and updates context accordingly
- **Smart Indicators**: Uses pronouns (it, this, that) and transition words to detect follow-ups

---

## Architecture

### Components

#### 1. Context Extractor (`orchestration/context_manager/context_extractor.py`)
Extracts structured context from conversation history using pattern matching:

```python
class ConversationContextExtractor:
    """Extracts context from conversation history"""
    
    # Repository patterns
    REPO_PATTERNS = [
        r'(?:repo|repository)\s+([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',
        r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',  # owner/repo
        r'github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',
    ]
    
    @classmethod
    def extract_context(cls, conversation_history, current_query=None):
        # Extracts: repositories, files, code entities, topics
        return ConversationContext(...)
```

**Extracted Context:**
- Current repository (most recently mentioned)
- Repository history (last 5 mentioned)
- File paths (last 10 mentioned)
- Code entities (functions, classes - last 10)
- Topics (authentication, API, database, etc.)

#### 2. Context Manager (`orchestration/context_manager/context_manager.py`)
Orchestrates context injection and smart query augmentation:

```python
class ConversationContextManager:
    """Manages conversation context for multi-turn interactions"""
    
    def augment_query_with_context(
        self, 
        query: str, 
        conversation_history: List[Dict]
    ) -> tuple[str, ConversationContext]:
        # Extract context
        context = self.extractor.extract_context(history, query)
        
        # Decide if augmentation needed
        if self._needs_context_augmentation(query, context):
            # Build augmented query
            return self._build_augmented_query(query, context), context
        
        return query, context
```

**Augmentation Logic:**
- Detects follow-up indicators (it, this, that, same, also, etc.)
- Checks for code queries without explicit repository
- Handles short queries with existing context
- Prepends repository context when needed

#### 3. Context Models (`orchestration/context_manager/models.py`)
Structured data models for context management:

```python
class ConversationContext(BaseModel):
    current_repository: Optional[str]
    repositories_mentioned: List[str]
    files_mentioned: List[str]
    code_entities: List[str]
    topics: List[str]
    features: List[str]
    tasks: List[str]
    last_query_type: Optional[str]
    conversation_depth: int
```

---

## Integration Flow

### 1. Frontend → Backend
**LLM Testing UI** (`frontend/src/components/Panels/LLMTestPanel.tsx`):
```typescript
const conversationHistory = messages.map(msg => ({
  role: msg.role,
  content: msg.content
}));

const result = await apiClient.testLLM(
  messageText, 
  provider, 
  showDetails, 
  model, 
  conversationHistory  // ← Sent to backend
);
```

### 2. Backend Processing
**API Endpoint** (`interfaces/http_api.py`):
```python
@app.post("/api/test/llm")
async def test_llm(
    prompt: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None
):
    if conversation_history:
        context_manager = ConversationContextManager()
        prompt, context = context_manager.augment_query_with_context(
            query=prompt,
            conversation_history=conversation_history
        )
    
    # Route to GitHub-LLM Orchestrator with augmented prompt
```

### 3. GitHub-LLM Orchestration
The augmented query flows through the existing pipeline:
```
Augmented Query → GitHub Query Detector → GitHub-LLM Orchestrator → Vector DB Search → LLM Response
```

---

## Usage Examples

### Example 1: Repository Context Persistence

**Conversation Flow:**
```
User: "repo AM-Portfolio/ai-bots show me the API implementation"
AI: [Shows API implementation from repository]

User: "what about error handling?"
→ Augmented to: "In repository AM-Portfolio/ai-bots: what about error handling?"
AI: [Shows error handling from same repository]

User: "explain the authentication service"
→ Augmented to: "In repository AM-Portfolio/ai-bots: explain the authentication service"
AI: [Shows auth service from repository]
```

### Example 2: File Context

**Conversation Flow:**
```
User: "in repo AM-Portfolio/ai-bots explain main.py"
AI: [Explains main.py]

User: "what functions does it have?"
→ Context: previous file = main.py, repo = AM-Portfolio/ai-bots
AI: [Lists functions in main.py from repository]
```

### Example 3: Topic Context

**Conversation Flow:**
```
User: "show me database models in AM-Portfolio/ai-bots"
AI: [Shows database models]

User: "how is authentication handled?"
→ Context: same repository, topic shift to authentication
AI: [Shows authentication implementation from repository]
```

### Example 4: Context Switching

**Conversation Flow:**
```
User: "repo AM-Portfolio/ai-bots show API routes"
AI: [Shows API routes from ai-bots]

User: "repo AM-Portfolio/another-project what's the API structure?"
→ Context switches to new repository
AI: [Shows API from another-project]

User: "does it have error handling?"
→ Uses new repository context (another-project)
AI: [Shows error handling from another-project]
```

---

## Follow-up Detection

### Indicators That Trigger Context Injection

**Pronouns:**
- "it", "this", "that", "there", "these", "those"

**Continuation Words:**
- "same", "also", "too", "as well"
- "next", "another", "other", "more"

**Question Patterns:**
- "what about...", "how about...", "tell me about..."

**Code Queries Without Repo:**
- "function", "class", "method", "api", "endpoint"
- "file", "code", "implementation", "show me", "explain"

### When Augmentation is NOT Applied

- Query explicitly mentions a repository
- Query contains full owner/repo format
- Query is long (>20 chars) and self-contained
- No existing repository context in conversation

---

## Context Lifecycle

### Per-Conversation Context
- **Storage**: In-memory during active conversation
- **Reset**: When user clicks "New Chat" or clears chat
- **Persistence**: Saved with conversation history in database

### Context Limits (Prevent Bloat)
- **Repositories**: Last 5 mentioned
- **Files**: Last 10 mentioned
- **Code Entities**: Last 10 mentioned
- **Topics**: Last 5 topics

---

## API Reference

### Backend API

#### POST `/api/test/llm`

**Parameters:**
```python
{
  "prompt": str,              # User query
  "provider": str,            # LLM provider (together, azure)
  "model": str,               # Model name
  "show_thinking": bool,      # Show thinking process
  "conversation_history": [   # Optional conversation context
    {
      "role": "user",
      "content": "repo AM-Portfolio/ai-bots show API"
    },
    {
      "role": "assistant",
      "content": "Here's the API implementation..."
    }
  ]
}
```

**Response:**
```python
{
  "success": bool,
  "response": str,             # LLM response
  "provider": str,
  "github_orchestration_used": bool,
  "github_context": {
    "is_github_related": bool,
    "repository": str,
    "query_type": str
  }
}
```

### Frontend API

#### `apiClient.testLLM()`

```typescript
async testLLM(
  prompt: string,
  provider: Provider,
  showThinking: boolean,
  model: string,
  conversationHistory?: Array<{role: string, content: string}>
): Promise<LLMTestResponse>
```

---

## Implementation Details

### Pattern Matching

**Repository Extraction:**
```python
REPO_PATTERNS = [
    r'(?:repo|repository)\s+([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',
    r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',
    r'github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',
]
```

**File Path Extraction:**
```python
FILE_PATTERNS = [
    r'(?:file|path)\s+([a-zA-Z0-9_\-/\.]+\.[a-z]+)',
    r'([a-zA-Z0-9_\-/]+\.[a-z]{2,4})',
    r'`([a-zA-Z0-9_\-/\.]+)`',
]
```

**Code Entity Extraction:**
```python
CODE_ENTITY_PATTERNS = [
    r'(?:function|class|method)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
    r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # Python
    r'class\s+([A-Z][a-zA-Z0-9]*)',     # Class definition
]
```

---

## Logging

The context manager provides detailed logging for debugging:

```
🧠 Applying conversation context from 2 previous messages
🔍 Extracting context from 2 messages
📂 Extracted repository: AM-Portfolio/ai-bots
📄 Extracted file: main.py
🔧 Extracted code entity: FastAPI
📌 Extracted topic: api
✅ Context extraction complete: Repository: AM-Portfolio/ai-bots | Files: main.py | Topics: api
📌 Follow-up query detected with repository context
✨ Query augmented: 'what about error handling' → 'In repository AM-Portfolio/ai-bots: what about error handling'
```

---

## Benefits

### For Users
✅ **Natural Conversations**: Ask follow-up questions without repeating context  
✅ **Less Typing**: Mention repository once, not in every message  
✅ **Context Awareness**: LLM understands conversation flow  
✅ **Seamless Experience**: Works transparently in background

### For Developers
✅ **Modular Design**: Context manager is independent module  
✅ **Easy to Extend**: Add new context types easily  
✅ **Comprehensive Logging**: Debug context extraction  
✅ **Type Safety**: Strong Pydantic models

---

## Future Enhancements

### Potential Improvements
1. **Persistent Context Storage**: Save context across sessions
2. **Cross-Repository Context**: "Compare authentication in repo A vs repo B"
3. **Temporal Context**: "Show me what changed since yesterday"
4. **User Preferences**: Learn user's preferred repositories
5. **Advanced Topic Detection**: Use ML for better topic extraction
6. **Context Visualization**: Show active context in UI
7. **Manual Context Control**: Let users manually set/clear context

---

## Testing

### Manual Test Scenarios

**Test 1: Basic Follow-up**
```
1. "repo AM-Portfolio/ai-bots show me API routes"
2. "what about authentication?"
   Expected: Returns auth from ai-bots repository
```

**Test 2: Multi-Turn**
```
1. "repo AM-Portfolio/ai-bots explain main.py"
2. "what functions does it have?"
3. "show me the FastAPI setup"
   Expected: All queries use ai-bots context
```

**Test 3: Context Switch**
```
1. "repo AM-Portfolio/ai-bots show API"
2. "repo AM-Portfolio/another-repo show API"
3. "what about error handling?"
   Expected: Uses another-repo (most recent)
```

**Test 4: Short Query**
```
1. "repo AM-Portfolio/ai-bots show database models"
2. "tests?"
   Expected: Augmented to ask about tests in ai-bots
```

### Verification
- Check backend logs for context extraction
- Verify query augmentation in logs
- Confirm GitHub-LLM orchestrator receives correct repository
- Validate Vector DB searches correct repository

---

## Troubleshooting

### Issue: Context Not Applied

**Symptoms:**
- Follow-up queries don't use previous repository
- LLM asks which repository

**Diagnosis:**
```bash
# Check logs for context extraction
grep "Extracting context" /tmp/logs/AI_Dev_Agent_*.log

# Check if query was augmented
grep "Query augmented" /tmp/logs/AI_Dev_Agent_*.log
```

**Solutions:**
1. Ensure conversation history is being sent
2. Check browser console for API errors
3. Verify repository was extracted from first message
4. Check follow-up indicators are present

### Issue: Wrong Repository Context

**Symptoms:**
- Query uses old repository instead of most recent

**Diagnosis:**
- Context manager uses **most recent** repository mentioned
- Check if new repository was mentioned in query

**Solution:**
- Explicitly mention repository to switch context
- Use "repo owner/name" format

### Issue: Over-Aggressive Augmentation

**Symptoms:**
- Context injected when not needed
- Queries become too long

**Solution:**
- The `_needs_context_augmentation()` method has filters:
  - Doesn't augment if query has explicit repo
  - Doesn't augment long self-contained queries
  - Only augments with follow-up indicators

---

## Related Features

- **GitHub Query Detection** (`shared/utils/github_query_detector.py`)
- **GitHub-LLM Orchestrator** (`orchestration/github_llm/query_orchestrator.py`)
- **Vector DB Semantic Search** (`shared/vector_db/`)
- **Chat History Management** (`interfaces/http_api.py` - conversation endpoints)

---

## Conclusion

The Conversational Context Manager transforms the LLM Testing UI from a stateless query interface into an intelligent conversational assistant that remembers context and understands follow-up questions. This significantly improves user experience and reduces repetitive typing while maintaining full transparency through comprehensive logging.

For questions or issues, check the logs or refer to the architecture documentation.
