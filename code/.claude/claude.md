# Claude Code Preferences - PipeLineServices

## Communication Style

### Documentation and Reports
- **DO NOT** create summary reports, verification reports, or documentation files unless explicitly requested by the user
- When work is complete, provide a brief verbal summary in the chat response instead
- Only create markdown files when the user specifically asks for documentation
- Focus on doing the work, not documenting that the work was done

### Code Changes
- Make changes directly and report what was done
- Show relevant output (like health check JSON) directly in chat
- Avoid creating "before/after" comparison documents

## Examples

### ❌ Don't Do This:
```
User: "Fix the version numbers"
Assistant: *fixes versions* "I've created VERSION_VERIFICATION.md with all the details..."
```

### ✅ Do This Instead:
```
User: "Fix the version numbers"
Assistant: *fixes versions* "Done! All services now show v1.0.0:
- Chunking: 5.0.0 → 1.0.0
- Metadata: 3.0.0 → 1.0.0
- Embeddings: 3.0.1 → 1.0.0
All services tested and healthy."
```

## When Documentation IS Appropriate
- User explicitly asks: "Create a document", "Write a report", "Document this"
- Project requires formal documentation (README, API docs, etc.)
- User asks for something to share with others

## Project-Specific Notes
- This is a microservices RAG pipeline
- Services communicate via REST APIs on ports 8060-8064
- All services are currently at v1.0.0
- SSH tunnel required for Milvus/LLM Gateway access
