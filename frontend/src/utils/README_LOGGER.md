# Frontend Activity Logger

A reactive logging system for tracking user actions and system events throughout the application.

## 🎯 Purpose

The logger provides:
1. **Real-time visibility** into what's happening in the frontend
2. **Debugging support** with categorized, filterable logs
3. **Performance tracking** with automatic timing
4. **User-friendly log viewer** with expandable details

## 🏗️ Architecture

```
┌─────────────────────────┐
│   React Components      │
│   (Chat, Voice, etc)    │
└───────────┬─────────────┘
            │
            │ logger.chat.info()
            │ logger.voice.debug()
            │ logger.api.track()
            ▼
┌─────────────────────────┐
│   Logger System         │
│   (logger.ts)           │
└───────────┬─────────────┘
            │
            ├─► Zustand Store (reactive state)
            ├─► Console output
            └─► LogViewer component
```

## 📦 Components

### 1. Logger Utility (`logger.ts`)

**Pre-configured loggers:**
- `logger.chat` - Chat message flow
- `logger.voice` - Voice recognition & synthesis
- `logger.integrations` - External service connections
- `logger.api` - HTTP API calls
- `logger.orchestrator` - Document orchestration
- `logger.llm` - LLM provider interactions
- `logger.ui` - UI navigation & state

**Log Levels:**
- `debug` - Detailed debugging information
- `info` - General information
- `warn` - Warning messages
- `error` - Error conditions
- `success` - Successful operations

### 2. LogViewer Component

- **Floating button** in bottom-right corner
- **Badge counter** showing total log entries
- **Filter by level** (debug, info, warn, error, success)
- **Filter by category** (Chat, Voice, API, etc.)
- **Expandable entries** for detailed data
- **Auto-scroll** to latest logs
- **Terminal-style UI** with color coding

## 💻 Usage Examples

### Basic Logging

```typescript
import { logger } from '../../utils/logger';

// Info message
logger.chat.info('User sent message');

// Debug message with data
logger.api.debug('API request', { 
  endpoint: '/api/chat',
  method: 'POST'
});

// Error logging
logger.llm.error('LLM call failed', { 
  error: 'Connection timeout' 
});

// Success message
logger.chat.success('Message delivered');

// Warning
logger.voice.warn('Microphone permission denied');
```

### Performance Tracking

Use the `.track()` method to automatically time operations:

```typescript
// Automatically logs start, duration, and success/failure
await logger.chat.track('Load conversation', async () => {
  const response = await fetch(`/api/conversations/${id}`);
  const data = await response.json();
  return data;
});

// Output:
// ℹ️  [Chat] Starting: Load conversation
// ✅ [Chat] Completed: Load conversation { duration: "450ms" }
```

### Integration Examples

**Chat Flow:**
```typescript
const handleSend = async () => {
  logger.chat.info('Sending message to together', { 
    messageLength: message.length,
    streaming: true
  });

  try {
    logger.llm.info('Calling together provider');
    const result = await apiClient.testLLM(message, 'together');
    
    logger.llm.success('Response received from together', { 
      duration: '2.5s',
      responseLength: 450
    });
    
    logger.chat.success('Message completed in 2.5s');
  } catch (error) {
    logger.chat.error('Failed to send message', { error });
  }
};
```

**Voice Recognition:**
```typescript
const toggleVoiceInput = () => {
  if (isListening) {
    logger.voice.info('Stopping voice recognition');
    recognition.stop();
  } else {
    logger.voice.info('Starting voice recognition');
    recognition.start();
  }
};
```

**Integration Connection:**
```typescript
const connectToGitHub = async () => {
  await logger.integrations.track('Connect to GitHub', async () => {
    await githubWrapper.connect();
    logger.integrations.info('GitHub connected successfully');
  });
};
```

## 🎨 Log Categories

### Chat
Tracks conversation flow:
- Message sending/receiving
- Conversation loading/saving
- Provider selection
- Response processing

### Voice
Tracks voice features:
- Speech recognition start/stop
- Voice synthesis
- Microphone permissions
- Audio playback

### Integrations
Tracks external services:
- Connection attempts
- Authentication
- API calls to integrations
- Service status changes

### API
Tracks HTTP requests:
- API endpoint calls
- Request/response data
- Error handling
- Network issues

### LLM
Tracks LLM interactions:
- Provider calls (Together AI, Azure)
- Response times
- Token usage
- Fallback attempts

### Orchestrator
Tracks document workflows:
- GitHub commits
- Confluence publishing
- Jira ticket creation
- Pipeline execution

### UI
Tracks user interface:
- Tab navigation
- Modal open/close
- Form submissions
- Component lifecycle

## 📊 LogViewer Interface

### Features

1. **Floating Button**
   - Click to open/close log viewer
   - Badge shows total log count
   - Positioned in bottom-right corner

2. **Filters**
   - **Level filter**: All, Debug, Info, Warn, Error, Success
   - **Category filter**: All, Chat, Voice, API, LLM, etc.
   - Real-time filtering as logs arrive

3. **Log Display**
   - Terminal-style dark UI
   - Color-coded by level:
     - 🔍 Debug (gray)
     - ℹ️ Info (blue)
     - ⚠️ Warning (yellow)
     - ❌ Error (red)
     - ✅ Success (green)
   - Timestamps for each entry
   - Category badges

4. **Expandable Details**
   - Click on logs with data to expand
   - Shows JSON-formatted details
   - Collapse/expand toggle

5. **Actions**
   - Clear all logs button
   - Auto-scroll to latest
   - Maximum 1000 logs (auto-cleanup)

## 🔧 Configuration

### Adding New Categories

```typescript
// In logger.ts
export const logger = {
  chat: createLogger('Chat'),
  voice: createLogger('Voice'),
  myNewCategory: createLogger('MyNewCategory'), // Add here
};
```

### Customizing Max Logs

```typescript
// In logger.ts
interface LogStore {
  maxLogs: number; // Change from 1000 to your desired limit
}
```

### Changing Console Output

```typescript
// In logger.ts addLog method
switch (level) {
  case 'debug':
    console.debug(formattedMessage, data || '');
    break;
  // Customize each level's console output
}
```

## 🎯 Best Practices

### 1. Use Appropriate Levels

- **debug**: Verbose, development-only information
- **info**: Standard operational messages
- **warn**: Potential issues that don't block operation
- **error**: Errors that need attention
- **success**: Confirmation of successful operations

### 2. Add Contextual Data

```typescript
// Good ✅
logger.chat.info('Message sent', { 
  messageId: '123',
  provider: 'together',
  duration: '1.2s'
});

// Bad ❌
logger.chat.info('Message sent');
```

### 3. Use Track for Performance

```typescript
// Automatically logs timing
await logger.api.track('Fetch users', async () => {
  return await fetchUsers();
});
```

### 4. Choose Right Category

```typescript
// Integration-related? Use integrations logger
logger.integrations.info('GitHub connected');

// API call? Use api logger
logger.api.debug('GET /api/users');

// User action? Use ui logger
logger.ui.info('Switched to Settings tab');
```

### 5. Log User Actions

Track important user flows:
```typescript
logger.ui.info('User clicked "New Chat" button');
logger.chat.info('Starting new conversation');
logger.chat.success('Conversation created');
```

## 🐛 Debugging Tips

### 1. Filter by Category

When debugging chat issues:
1. Open LogViewer
2. Select "Chat" category
3. Review the message flow

### 2. Check Timing

Look for slow operations:
```typescript
await logger.api.track('Load data', async () => {
  // Logs show exact duration
});
```

### 3. Expand Error Details

Click on error logs to see full error objects and stack traces.

### 4. Watch for Patterns

Multiple errors from same category? Focus debugging there.

## 📈 Performance Impact

- **Minimal overhead**: Logs are batched and don't block UI
- **Auto-cleanup**: Automatically removes old logs (max 1000)
- **Console passthrough**: All logs also go to browser console
- **Reactive updates**: Uses Zustand for efficient state management

## 🚀 Future Enhancements

Potential improvements:
- Export logs to file
- Remote logging to backend
- Search/filter by message text
- Customizable color schemes
- Log level persistence
- Integration with error tracking services
