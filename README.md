# Degang Simulator

AI-powered Chinese text-to-speech application featuring Guo Degang's voice simulation.

## Features

- **AI Chat**: Interactive chat with web search and page reading capabilities
- **Text-to-Speech**: Generate audio using Chinese TTS with Guo Degang's voice
- **Story Generation**: Create stories, jokes, and poems with AI assistance

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your SUPER_MIND_API_KEY
```

3. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Deployment

This application is configured for deployment to `ai-builders.space`. See `Prompts/deployment-prompt.md` for details.

## License

MIT
