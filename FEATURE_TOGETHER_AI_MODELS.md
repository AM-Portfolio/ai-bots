# Together AI Multiple Model Support

## Feature Overview
Added support for three Together AI models in the LLM Testing UI, allowing users to choose between different models under the same Together AI provider.

## Available Models

### 1. Llama-3.3-70B (Default)
- **Model ID:** `meta-llama/Llama-3.3-70B-Instruct-Turbo`
- **Description:** Meta's flagship instruction-tuned model
- **Best For:** General-purpose tasks, conversational AI, instruction following

### 2. DeepSeek-R1
- **Model ID:** `deepseek-ai/DeepSeek-R1`
- **Description:** DeepSeek's reasoning model
- **Best For:** Complex reasoning, problem-solving, analytical tasks

### 3. Qwen3-Coder
- **Model ID:** `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8`
- **Description:** Alibaba's specialized coding model
- **Best For:** Code generation, code explanation, programming tasks

### 4. GPT-4 (Azure)
- **Provider:** Azure OpenAI
- **Description:** Microsoft Azure's GPT-4 deployment
- **Best For:** Enterprise-grade tasks, complex analysis

## Implementation Details

### Backend Changes

#### 1. HTTP API Endpoint (`interfaces/http_api.py`)
- Added `model` parameter to `/api/test/llm` endpoint
- Default model: `meta-llama/Llama-3.3-70B-Instruct-Turbo`
- Model parameter is passed through to resilient orchestrator

```python
@app.post("/api/test/llm")
async def test_llm(
    prompt: str, 
    provider: str = "together", 
    model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo", 
    show_thinking: bool = False
)
```

#### 2. Resilient Orchestrator (`shared/llm_providers/resilient_orchestrator.py`)
- Updated `chat_completion_with_fallback()` to accept `model` parameter
- Updated `_try_provider()` to pass model to LLMFactory
- Model is automatically applied to Together AI provider instances

```python
async def chat_completion_with_fallback(
    self,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_retries: int = 2,
    preferred_provider: Optional[str] = None,
    model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
) -> Tuple[str, Dict[str, Any]]:
```

#### 3. LLM Factory (`shared/llm_providers/factory.py`)
- Already supported `together_model` parameter (no changes needed)
- Passes model to TogetherAIProvider constructor

#### 4. Together AI Provider (`shared/llm_providers/together_provider.py`)
- Already supported `model` parameter in constructor (no changes needed)
- Uses the model in all chat completion calls

### Frontend Changes

#### 1. LLM Test Panel (`frontend/src/components/Panels/LLMTestPanel.tsx`)
- Added `model` state variable with default value
- Updated dropdown to show all four options:
  - Llama-3.3-70B
  - DeepSeek-R1
  - Qwen3-Coder
  - GPT-4 (Azure)
- Model selection automatically sets provider to "together" for Together AI models
- Azure option sets provider to "azure"

```typescript
const [model, setModel] = useState('meta-llama/Llama-3.3-70B-Instruct-Turbo');

<select
  value={provider === 'together' ? model : provider}
  onChange={(e) => {
    const value = e.target.value;
    if (value === 'azure') {
      setProvider('azure');
    } else {
      setProvider('together');
      setModel(value);
    }
  }}
>
  <option value="meta-llama/Llama-3.3-70B-Instruct-Turbo">Llama-3.3-70B</option>
  <option value="deepseek-ai/DeepSeek-R1">DeepSeek-R1</option>
  <option value="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8">Qwen3-Coder</option>
  <option value="azure">GPT-4 (Azure)</option>
</select>
```

#### 2. API Client (`frontend/src/services/api.ts`)
- Updated `testLLM()` to accept `model` parameter
- Model is sent as query parameter to backend

```typescript
async testLLM(
  prompt: string, 
  provider: Provider = 'together', 
  showThinking: boolean = false, 
  model: string = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'
): Promise<LLMTestResponse>
```

### Bug Fixes
- Fixed unused import warning in `LogViewer.tsx`
- Removed `LogEntry` from imports (was imported but never used)

## Usage

### From LLM Testing UI
1. Navigate to "LLM Testing" tab
2. Select your preferred model from the dropdown (bottom left)
3. Type your prompt
4. Click send or press Enter

### From API (curl)
```bash
# Test with Llama-3.3-70B (default)
curl -X POST "http://localhost:8000/api/test/llm?prompt=Hello&provider=together&model=meta-llama%2FLlama-3.3-70B-Instruct-Turbo"

# Test with DeepSeek-R1
curl -X POST "http://localhost:8000/api/test/llm?prompt=Solve%20this%20problem&provider=together&model=deepseek-ai%2FDeepSeek-R1"

# Test with Qwen3-Coder
curl -X POST "http://localhost:8000/api/test/llm?prompt=Write%20a%20function&provider=together&model=Qwen%2FQwen3-Coder-480B-A35B-Instruct-FP8"

# Test with GPT-4 (Azure)
curl -X POST "http://localhost:8000/api/test/llm?prompt=Analyze%20this&provider=azure"
```

### From Python/JavaScript
```python
# Python example
import requests

response = requests.post(
    "http://localhost:8000/api/test/llm",
    params={
        "prompt": "Write a Python function to sort a list",
        "provider": "together",
        "model": "Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8",
        "show_thinking": True
    }
)
print(response.json())
```

```javascript
// JavaScript example
const response = await fetch(
  '/api/test/llm?' + new URLSearchParams({
    prompt: 'Explain quantum computing',
    provider: 'together',
    model: 'deepseek-ai/DeepSeek-R1',
    show_thinking: 'true'
  }),
  { method: 'POST' }
);
const data = await response.json();
console.log(data.response);
```

## Benefits

### 1. Model Specialization
- **Coding Tasks:** Use Qwen3-Coder for code generation and explanation
- **Reasoning Tasks:** Use DeepSeek-R1 for complex problem-solving
- **General Tasks:** Use Llama-3.3-70B for balanced performance
- **Enterprise Tasks:** Use GPT-4 (Azure) for production workloads

### 2. Cost Optimization
- Different models have different pricing tiers
- Choose the right model for your use case to optimize costs

### 3. Performance Comparison
- Easily compare outputs from different models
- Switch between models without changing code

### 4. Fallback Resilience
- If one Together AI model fails, the system can fall back to Azure OpenAI
- Circuit breaker pattern prevents repeated failures

## Architecture Flow

```
User Input (LLM Testing UI)
    ↓
Select Model from Dropdown (Llama-3.3-70B / DeepSeek-R1 / Qwen3-Coder / GPT-4)
    ↓
Frontend API Client sends: prompt, provider, model
    ↓
Backend HTTP API (/api/test/llm) receives parameters
    ↓
Routes to Resilient Orchestrator with model parameter
    ↓
Resilient Orchestrator creates provider via LLMFactory
    ↓
LLMFactory creates TogetherAIProvider with specified model
    ↓
TogetherAIProvider makes API call to Together AI with model ID
    ↓
Response returned through the chain
    ↓
UI displays response with model metadata
```

## Testing

### Manual Testing Steps
1. Open LLM Testing UI
2. Select "Llama-3.3-70B" - should work (default model)
3. Select "DeepSeek-R1" - should work with DeepSeek model
4. Select "Qwen3-Coder" - should work with Qwen coding model
5. Select "GPT-4 (Azure)" - should switch to Azure provider
6. Verify each model responds appropriately to prompts

### API Testing
```bash
# Test all models
for model in "meta-llama/Llama-3.3-70B-Instruct-Turbo" "deepseek-ai/DeepSeek-R1" "Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8"; do
    echo "Testing $model..."
    curl -X POST "http://localhost:8000/api/test/llm?prompt=Hello&provider=together&model=$(echo $model | jq -sRr @uri)"
    echo -e "\n---\n"
done
```

## Future Enhancements

### Potential Improvements
1. **Model Parameters UI:** Add sliders for temperature, max_tokens, top_p
2. **Model Comparison:** Side-by-side comparison of responses from different models
3. **Model Statistics:** Track usage, costs, and performance per model
4. **Custom Model Support:** Allow users to add custom Together AI models
5. **Model Presets:** Save favorite model configurations
6. **A/B Testing:** Automatically route queries to different models for testing

### Configuration Management
Consider adding a configuration file for model management:
```json
{
  "together_models": [
    {
      "id": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
      "name": "Llama-3.3-70B",
      "description": "General-purpose instruction model",
      "max_tokens": 4096,
      "cost_per_1k_tokens": 0.002
    },
    {
      "id": "deepseek-ai/DeepSeek-R1",
      "name": "DeepSeek-R1",
      "description": "Reasoning-optimized model",
      "max_tokens": 8192,
      "cost_per_1k_tokens": 0.003
    }
  ]
}
```

## Troubleshooting

### Issue: Model not found
**Cause:** Together AI model ID is incorrect or model is not available

**Solution:** Verify model ID at https://docs.together.ai/docs/inference-models

### Issue: Fallback to Azure even with valid Together AI key
**Cause:** Selected model might not be accessible with your API tier

**Solution:** Check your Together AI account for model access permissions

### Issue: Slow response times
**Cause:** Some models (like Qwen3-Coder-480B) are very large

**Solution:** Use smaller models (Llama-3.3-70B) for faster responses

## Documentation References

- [Together AI Models](https://docs.together.ai/docs/inference-models)
- [DeepSeek Documentation](https://platform.deepseek.com/)
- [Qwen Documentation](https://qwen.readthedocs.io/)
- [Vector DB Usage Guide](VECTOR_DB_USAGE.md)

---

**Feature Completed:** October 18, 2025  
**Version:** 1.0.0
