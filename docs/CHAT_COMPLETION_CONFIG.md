# Azure Chat Completion Configuration Guide

## Overview

This guide explains the unified configuration system for Azure OpenAI chat completion models in the ai-bots application.

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Azure OpenAI Base Configuration
AZURE_OPENAI_ENDPOINT=https://munis-mgzdcoho-eastus2.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here

# Chat Completion Models (Common Configuration)
AZURE_CHAT_MODEL=gpt-4.1-mini                    # Default chat model
AZURE_CHAT_API_VERSION=2025-01-01-preview        # Chat API version

# Specific Deployments (Optional)
AZURE_MODEL_ROUTER_DEPLOYMENT=model-router       # Intelligent routing
AZURE_GPT4O_TRANSCRIBE_DEPLOYMENT=gpt-4o-transcribe-diarize
AZURE_GPT_AUDIO_MINI_DEPLOYMENT=gpt-audio-mini
```

### Configuration Priority

The system uses the following priority for chat model selection:

1. **Explicit model parameter**: `model="gpt-4.1-mini"` in method call
2. **AZURE_CHAT_MODEL**: Environment variable
3. **AZURE_OPENAI_DEPLOYMENT_NAME**: Fallback for backward compatibility
4. **Default**: `gpt-4.1-mini`

## Usage

### Method 1: Default Chat Model

Uses `AZURE_CHAT_MODEL` from configuration:

```python
from shared.azure_services.model_deployment_service import AzureModelDeploymentService

service = AzureModelDeploymentService()

# Uses default chat model (gpt-4.1-mini)
response = await service.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7
)
```

### Method 2: Model Router (Legacy)

Uses intelligent routing to select best model:

```python
# Routes to best model automatically
response = await service.chat_with_model_router(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)
```

### Method 3: Explicit Model Override

Specify exact model to use:

```python
# Use specific model
response = await service.chat_completion(
    messages=[...],
    model="gpt-4.1-mini",  # Override default
    temperature=0.7
)
```

## URL Construction

The service automatically constructs the correct endpoint URL:

```
{endpoint}/openai/deployments/{model}/chat/completions?api-version={version}
```

For example:
```
https://munis-mgzdcoho-eastus2.cognitiveservices.azure.com/openai/deployments/gpt-4.1-mini/chat/completions?api-version=2025-01-01-preview
```

## Available Models

### gpt-4.1-mini
- **Purpose**: Lightweight, fast chat completion
- **API Version**: 2025-01-01-preview
- **Capabilities**: Chat, multi-turn conversations, function calling
- **Best For**: General chat, fast responses, cost-effective

### model-router
- **Purpose**: Intelligent model selection
- **Capabilities**: Automatic routing to best GPT model
- **Best For**: Complex queries needing optimal model selection

## Configuration Class

### shared/config.py

```python
class Settings(BaseSettings):
    # Chat Completion Models (Common Configuration)
    azure_chat_model: Optional[str] = "gpt-4.1-mini"
    azure_chat_api_version: Optional[str] = "2025-01-01-preview"
    
    # Specific Deployments
    azure_model_router_deployment: Optional[str] = None
```

## Service Methods

### `chat_completion()`

**Common method for all Azure chat models**

```python
async def chat_completion(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None
) -> str
```

**Parameters:**
- `messages`: Chat messages in OpenAI format
- `temperature`: Sampling temperature (0-2)
- `max_tokens`: Maximum tokens to generate
- `model`: Optional model override

**Returns:** Assistant's response text

### `chat_with_model_router()`

**Legacy method for model-router deployment**

```python
async def chat_with_model_router(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str
```

## Migration Guide

### Old Approach (Hardcoded)
```python
response = await self.client.chat.completions.create(
    model="model-router",  # Hardcoded
    messages=messages
)
```

### New Approach (Config-Driven)
```python
# Uses AZURE_CHAT_MODEL from .env
response = await service.chat_completion(
    messages=messages
)

# Or override with specific model
response = await service.chat_completion(
    messages=messages,
    model="gpt-4.1-mini"
)
```

## Deployment Info

Get information about configured deployments:

```python
info = await service.get_deployment_info()
print(info["deployments"]["chat_model"])
# {
#   "name": "gpt-4.1-mini",
#   "api_version": "2025-01-01-preview",
#   "capabilities": ["chat_completion", "multi_turn", "function_calling"],
#   "url": "https://.../.../chat/completions?api-version=..."
# }
```

## Testing

Run the test suite:

```bash
python test_chat_completion_config.py
```

## Best Practices

1. **Use Environment Variables**: Store all model names in `.env`
2. **Default to Common Config**: Use `chat_completion()` for standard chat
3. **Explicit When Needed**: Override model only when necessary
4. **Log Model Selection**: Service automatically logs which model is used
5. **Handle Errors**: Wrap calls in try-except for proper error handling

## Error Handling

### 404 - Resource Not Found
**Cause**: Deployment name doesn't match Azure configuration

**Solution**: 
1. Check Azure AI Foundry for exact deployment name
2. Update `AZURE_CHAT_MODEL` in `.env`
3. Verify deployment is active in Azure

### 401 - Unauthorized
**Cause**: Invalid API key

**Solution**: Update `AZURE_OPENAI_API_KEY` in `.env`

### 429 - Rate Limit
**Cause**: Too many requests

**Solution**: Implement retry logic with exponential backoff

## Integration with LLM Factory

The chat completion configuration works seamlessly with the LLM provider factory:

```python
from shared.llm import LLM

# Auto-detects Azure and uses AZURE_CHAT_MODEL
llm = LLM()
response = await llm.generate("Hello, how are you?")
```

## Benefits

✅ **Consistent Configuration**: Single source of truth for chat models  
✅ **Flexible Deployment**: Easy to switch between models  
✅ **Backward Compatible**: Legacy methods still work  
✅ **URL Construction**: Automatic endpoint URL generation  
✅ **Error Handling**: Clear logging and error messages  
✅ **Type Safety**: Full type hints and validation  

## See Also

- [LLM Provider Auto-Detection](./LLM_PROVIDER_AUTO_DETECTION.md)
- [Integration Plan](./INTEGRATION_PLAN.md)
- [Architecture Diagrams](./ARCHITECTURE_DIAGRAMS.md)
