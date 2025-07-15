# Development Setup

## Prerequisites

- Python 3.11+
- Docker
- MongoDB (via Docker)
- Redis (via Docker)

## Knowledge Base Setup

The development knowledge base has been initialized with:
- Documentation from: /Users/filip/Documents/Source/VideoCommentator-MonoRepo
- PDF blueprints from: /Users/filip/Documents/Source/video-intelligence-project/research

To query the knowledge base:
```bash
source venv/bin/activate
./dev-cli ask "your question here"
```

## Next Steps

1. Run Claude CLI to implement the knowledge extraction scripts
2. Populate the knowledge base
3. Start implementing core services

See `CLAUDE_INSTRUCTIONS.md` for detailed implementation guidance.
