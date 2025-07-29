# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is an AI SDK laboratory project with a monorepo structure containing:

- **frontend/**: Next.js 15 React application using the Vercel AI SDK
  - Uses `@ai-sdk/react` for chat functionality with the `useChat` hook
  - Built with TypeScript, Tailwind CSS, and React 19
  - Standard Next.js App Router structure in `src/app/`

- **backend/**: FastAPI Python backend
  - Built with FastAPI, LangChain, and OpenAI integration
  - Currently minimal with basic structure in `src/api/` and `src/model/`
  - Uses uv for Python dependency management

## Development Commands

### Frontend (Next.js)
```bash
cd frontend
pnpm dev          # Start development server on http://localhost:3000
pnpm build        # Build for production
pnpm start        # Start production server
pnpm lint         # Run ESLint
```

### Backend (Python)
```bash
cd backend
uv run python main.py    # Run the basic Python script
```

## Key Technologies

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Vercel AI SDK
- **Backend**: FastAPI, LangChain, Python 3.10+
- **Package Management**: pnpm (frontend), uv (backend)

## Architecture Notes

The project appears to be set up for AI chat integration experiments. The `ui-integration.md` file contains comprehensive documentation about implementing production-ready chat components using Vercel's `useChat` hook, including:

- Custom backend integration patterns
- Data stream protocol implementation
- Authentication and security patterns
- Reusable component architecture
- Enterprise deployment considerations

When working with chat functionality, refer to the patterns and examples in `ui-integration.md` for best practices on integrating with custom backends and implementing secure, scalable chat interfaces.

## Important Files

- `ui-integration.md`: Comprehensive guide for AI chat integration patterns
- `frontend/src/app/page.tsx`: Main Next.js page component
- `backend/main.py`: Basic Python entry point