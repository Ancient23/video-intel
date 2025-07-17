import os
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from rag.dev_assistant import DevelopmentAssistant
import motor.motor_asyncio
from beanie import init_beanie
import asyncio
import sys

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import ProjectKnowledge


class ClaudeContextGenerator:
    """Generates context files for Claude CLI"""
    
    def __init__(self):
        self.assistant = None
    
    def generate_context(self, topic: str) -> str:
        """Generate context for a specific topic"""
        
        # Initialize assistant lazily
        if self.assistant is None:
            self.assistant = DevelopmentAssistant()
        
        # Query knowledge base
        patterns = self.assistant.query_patterns(topic)
        
        # Query for specific architectural decisions
        decisions = self.assistant.query_patterns(f"{topic} architectural decisions", category="architectural_decisions")
        
        # Query for known issues
        issues = self.assistant.query_patterns(f"{topic} known issues problems", category="known_issues")
        
        # Get MongoDB data
        mongodb_context = asyncio.run(self._get_mongodb_context(topic))
        
        context = f"""# Context for: {topic}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Overview
This context provides guidance for implementing {topic} based on best practices from NVIDIA blueprints and our knowledge base.

## Relevant Implementation Patterns
{patterns}

## Architectural Decisions
{decisions}

## Known Issues to Avoid
{issues}

## Code Examples from Knowledge Base
{mongodb_context.get('code_examples', 'No specific code examples found.')}

## Implementation Guidelines
- Always use Pydantic V2 patterns with proper field validators
- Follow the provider abstraction pattern from VideoCommentator
- Include proper error handling and retries
- Use structured logging with contextual information
- Cache expensive operations with proper TTLs
- Set worker memory limits to avoid OOM issues
- Validate S3 paths before using cached data

## Key Files to Reference
{mongodb_context.get('key_files', 'No specific files identified.')}

## Testing Considerations
- Mock external services (AWS, OpenAI, NVIDIA)
- Use pytest fixtures for common setups
- Test error handling and edge cases
- Verify memory usage under load

## Performance Tips
{mongodb_context.get('performance_tips', 'Follow general performance best practices.')}

## Related Documentation
- Video Intelligence PRD: docs/new/video-intelligence-prd.md
- Old VideoCommentator: /Users/filip/Documents/Source/VideoCommentator-MonoRepo
- NVIDIA Blueprints: dev-knowledge-base/docs/pdfs/
"""
        
        return context
    
    async def _get_mongodb_context(self, topic: str) -> Dict[str, str]:
        """Get additional context from MongoDB"""
        context = {
            "code_examples": "",
            "key_files": "",
            "performance_tips": ""
        }
        
        try:
            # Initialize MongoDB
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
            await init_beanie(
                database=client.dev_knowledge_base,
                document_models=[ProjectKnowledge]
            )
            
            # Search for relevant documents
            search_terms = topic.lower().split()
            
            # Find code examples
            code_items = await ProjectKnowledge.find(
                {"$or": [
                    {"title": {"$regex": term, "$options": "i"}} for term in search_terms
                ]},
                {"code_examples": {"$exists": True, "$ne": []}}
            ).limit(3).to_list()
            
            if code_items:
                examples = []
                for item in code_items:
                    if item.code_examples:
                        for example in item.code_examples[:1]:  # First example from each
                            examples.append(f"### From {item.source_file}\n```python\n{example.get('content', '')[:500]}...\n```")
                context["code_examples"] = "\n\n".join(examples)
            
            # Find key files
            file_items = await ProjectKnowledge.find(
                {"$or": [
                    {"title": {"$regex": term, "$options": "i"}} for term in search_terms
                ]},
                {"importance": {"$gte": 4}}
            ).sort("importance", -1).limit(5).to_list()
            
            if file_items:
                files = [f"- {item.source_file}: {item.title}" for item in file_items]
                context["key_files"] = "\n".join(files)
            
            # Find performance tips
            perf_items = await ProjectKnowledge.find(
                {"$and": [
                    {"$or": [{"content": {"$regex": "performance", "$options": "i"}},
                            {"content": {"$regex": "optimization", "$options": "i"}}]},
                    {"$or": [{"title": {"$regex": term, "$options": "i"}} for term in search_terms]}
                ]}
            ).limit(3).to_list()
            
            if perf_items:
                tips = []
                for item in perf_items:
                    # Extract performance-related sentences
                    content = item.content
                    sentences = content.split('.')
                    perf_sentences = [s.strip() for s in sentences 
                                    if any(word in s.lower() for word in ["performance", "optimization", "speed", "memory", "cache"])]
                    if perf_sentences:
                        tips.extend(perf_sentences[:2])
                
                if tips:
                    context["performance_tips"] = "\n- ".join([""] + tips[:5])
            
        except Exception as e:
            print(f"Error getting MongoDB context: {e}")
        
        return context
    
    def update_claude_instructions(self):
        """Update CLAUDE.md with latest knowledge"""
        claude_md_path = Path(__file__).parent.parent.parent / "CLAUDE.md"
        
        if not claude_md_path.exists():
            print(f"CLAUDE.md not found at {claude_md_path}")
            return
        
        # This is a placeholder - in a real implementation, you would:
        # 1. Load current CLAUDE.md
        # 2. Update specific sections with new patterns
        # 3. Save the updated version
        
        print("Update CLAUDE.md functionality not yet implemented")