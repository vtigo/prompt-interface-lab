# AI Chat Backend

A simple, reliable FastAPI backend for chat applications that integrates with the Vercel AI SDK. Built following conservative coding principles with emphasis on maintainability, error handling, and type safety.

## Features

- **Streaming Chat API**: Compatible with Vercel AI SDK's `useChat` hook
- **OpenAI Integration**: Uses LangChain for OpenAI model interaction
- **Type Safety**: Full Pydantic model validation
- **Error Handling**: Comprehensive error handling and logging
- **CORS Support**: Configured for frontend integration

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Run the server**:
   ```bash
   uv run python main.py
   ```

The server will start on `http://127.0.0.1:8000`.

## API Endpoints

### POST /api/chat
Streaming chat endpoint compatible with Vercel AI SDK.

**Request format**:
```json
{
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "id": "conversation-123"
}
```

**Response**: Streaming text in Vercel AI SDK format with headers:
- `Content-Type: text/plain; charset=utf-8`
- `x-vercel-ai-data-stream: v1`

### GET /health
Simple health check endpoint.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model to use |
| `OPENAI_TEMPERATURE` | `0.7` | Sampling temperature |
| `HOST` | `127.0.0.1` | Server host |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `info` | Logging level |
| `ENVIRONMENT` | `development` | Environment mode |

## Frontend Integration

This backend is designed to work with Vercel AI SDK's `useChat` hook:

```typescript
import { useChat } from '@ai-sdk/react';

const { messages, input, handleInputChange, handleSubmit } = useChat({
  api: 'http://127.0.0.1:8000/api/chat',
  streamProtocol: 'data'
});
```

## Architecture

The codebase follows conservative design principles:

- **`src/model/chat_agent.py`**: LangChain OpenAI integration
- **`src/api/models.py`**: Pydantic request/response models
- **`src/api/chat.py`**: FastAPI chat endpoint implementation
- **`main.py`**: Application setup and server configuration

## Error Handling

The backend implements comprehensive error handling:
- Input validation with clear error messages
- Graceful OpenAI API error handling
- Global exception handler for unexpected errors
- Structured logging for debugging