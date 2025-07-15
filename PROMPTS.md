# PROMPTS.md

This file provides reusable prompt templates for working with AI coding assistants (Claude Code, GitHub Copilot, Cursor, etc.) on the Video Intelligence Platform project.

⚠️ **IMPORTANT**: When updating this file, also update:
- CLAUDE.md
- Any future AI assistant configuration files

All AI assistant configuration files should be kept in sync to ensure consistent behavior across different coding environments.

## Quick Reference Guide

### How to Use These Templates

**Most Efficient Method:** Reference templates by name instead of copy-pasting.

#### Simple Reference:
```
Use the Implementation Plan Step Execution Template from PROMPTS.md for implementing video chunking.
```

#### Template Shortcuts:
- **impl-plan** → Implementation Plan Step Execution Template
- **impl-multi** → Multi-Step Implementation Session Template
- **refactor** → Basic Refactoring Template
- **bug** → Bug Investigation Template
- **feature** → New Feature Template
- **feature-provider** → Provider Integration Template
- **doc-sync** → Documentation Sync Template
- **test** → Test Implementation Template
- **arch** → Architecture Change Template
- **deploy** → Deployment Preparation Template
- **status-check** → Project Status Check Template
- **status-update** → MongoDB Status Update Template
- **knowledge-query** → Development Knowledge Base Query Template
- **knowledge-add** → Add Knowledge to Dev Database Template
- **next-task** → Get Next Implementation Task Template
- **debt-check** → Technical Debt Status Template
- **debt-add** → Add Technical Debt Item Template
- **debt-resolve** → Resolve Technical Debt Template

#### Example Usage:
```
Apply the status-check template from PROMPTS.md to see our current progress.
```

```
Use the impl-plan template for implementing the video chunking service.
```

#### Combining Templates:
```
For this task, combine:
1. Start with knowledge-query template to check existing patterns
2. Use feature template for the main implementation
3. Finish with status-update template to track progress
```

---

## Core Principles

All prompts should enforce:
1. **Query knowledge base first**: Always check dev-cli for patterns before implementing
2. **Update MongoDB status**: Track all progress in project status collection
3. **Follow PRD specifications**: Refer to docs/new/video-intelligence-prd.md
4. **Use existing patterns**: Reference old VideoCommentator code when applicable
5. **Document learnings**: Update knowledge base with new insights

---

## Project Status Management

### Project Status Check Template
```
Check the current project status and show me what needs to be done next.

Steps:
1. Query MongoDB project status:
   ```python
   python scripts/init_project_status.py
   ```
2. Use dev-cli to check for relevant patterns:
   ```bash
   source venv/bin/activate
   ./dev-cli ask "What are the current implementation priorities?"
   ```
3. Review PRD for current phase requirements:
   - Check `/docs/new/video-intelligence-prd.md`
   - Identify current phase tasks
4. Show me:
   - Current phase and progress
   - Component completion status
   - Active tasks
   - Blocked items
   - Next recommended steps
```

### MongoDB Status Update Template
```
Update project status after completing [task/component].

Task completed: [describe what was done]

Steps:
1. Update MongoDB status:
   - Mark component status if applicable
   - Add completed task to list
   - Remove from current tasks
   - Add any new notes or issues
2. Check for technical debt:
   - Review code for TODO/FIXME comments
   - Identify incomplete implementations
   - Note any hardcoded values or workarounds
   - Add items to technical debt tracking:
     ```python
     python scripts/init_technical_debt.py
     ```
3. Query knowledge base for related items:
   ```bash
   ./dev-cli ask "Any issues related to [component]?"
   ```
4. Update knowledge base if new patterns discovered:
   - Create markdown file in dev-knowledge-base/docs/
   - Document pattern/lesson learned
   - Run knowledge base ingestion
5. Report:
   - What was updated
   - Current phase progress
   - Any technical debt created
   - Next recommended tasks
```

### Get Next Implementation Task Template
```
What should I implement next based on our current progress?

Analysis:
1. Check current project status in MongoDB
2. Review PRD implementation phases
3. Query knowledge base for prerequisites:
   ```bash
   ./dev-cli ask "Prerequisites for [next component]"
   ```
4. Consider:
   - Dependencies between components
   - Current phase objectives
   - Blocked tasks that can be unblocked
   - Quick wins vs complex tasks
5. Recommend:
   - Next task with clear requirements
   - Estimated effort
   - Required knowledge/patterns
   - Success criteria
```

---

## Technical Debt Management

### Technical Debt Status Template
```
Show me the current technical debt status and high priority items.

Steps:
1. Query technical debt collection:
   ```python
   python scripts/init_technical_debt.py
   ```
2. Analyze report showing:
   - Total debt items and open items
   - Critical and high priority items
   - Estimated effort hours remaining
   - Items by category and severity
3. For critical/high items:
   - Show file locations and line numbers
   - Explain impact on system
   - Suggest resolution approach
4. Check if any debt blocks current tasks:
   - Cross-reference with project status
   - Identify dependencies
5. Recommend:
   - Which debt to address first
   - Quick wins (< 2 hours)
   - Items that unblock features
```

### Add Technical Debt Item Template
```
Add a new technical debt item for [issue/incomplete implementation].

Issue: [description]
Location: [file path and line numbers if applicable]
Severity: [critical/high/medium/low]
Category: [security/performance/incomplete/hardcoded/missing_integration/testing/documentation/error_handling/configuration/monitoring]

Steps:
1. Create debt item:
   ```python
   from backend.models import TechnicalDebt, TechnicalDebtItem, DebtSeverity, DebtCategory
   
   item = TechnicalDebtItem(
       id="[CATEGORY-NNN]",
       title="[Short descriptive title]",
       description="[Detailed description]",
       file_path="[path/to/file.py]",
       line_numbers=[line1, line2],
       category=DebtCategory.[CATEGORY],
       severity=DebtSeverity.[SEVERITY],
       estimated_effort_hours=[float],
       tags=["tag1", "tag2"]
   )
   ```
2. Add to technical debt document:
   - Specify component/service area
   - Update statistics
3. If discovered during implementation:
   - Add TODO/FIXME comment in code
   - Reference debt item ID
   ```python
   # TODO: [DEBT-ID] - Brief description
   # See technical debt tracking for full details
   ```
4. Update project status if this blocks features
5. Report debt item details and impact
```

### Resolve Technical Debt Template
```
Resolve technical debt item [DEBT-ID].

Debt ID: [ID from technical debt tracking]

Pre-resolution:
1. Query debt details:
   - Get full description and requirements
   - Check file locations
   - Review estimated effort
2. Check for related items:
   - Other debt in same component
   - Dependencies on this resolution
3. If from VideoCommentator:
   ```bash
   ./dev-cli ask "VideoCommentator [component] implementation"
   ```
   - Check if we can reuse existing code

Resolution:
1. Implement fix following patterns:
   - Use knowledge base guidance
   - Follow PRD specifications
   - Apply VideoCommentator patterns
2. Remove TODO/FIXME comments
3. Test thoroughly:
   - Unit tests for the fix
   - Integration tests if applicable
   - Verify no regressions
4. Update technical debt:
   - Mark item as resolved
   - Add resolution notes
   - Update statistics
5. If pattern discovered:
   - Add to knowledge base
   - Document for future
6. Report:
   - What was fixed
   - Any new debt discovered
   - Impact on system
```

---

## Knowledge Base Operations

### Development Knowledge Base Query Template
```
Query the knowledge base about [topic/component/pattern].

Topic: [what you want to know]

Steps:
1. Activate environment and query:
   ```bash
   source venv/bin/activate
   ./dev-cli ask "[your question]"
   ```
2. For implementation suggestions:
   ```bash
   ./dev-cli suggest "[component name]"
   ```
3. Check multiple related topics:
   - Patterns from VideoCommentator
   - NVIDIA blueprint insights
   - Known issues and solutions
   - Best practices
4. If no results, check:
   - Old VideoCommentator repo directly
   - PRD for specifications
   - MongoDB schemas for structure
```

### Add Knowledge to Dev Database Template
```
Add new knowledge/pattern to the development database.

Knowledge type: [Pattern/Lesson/Issue/Solution]
Component: [which component this relates to]

Steps:
1. Create knowledge document:
   ```bash
   cat > dev-knowledge-base/docs/new/[topic]-[date].md << EOF
   # [Title]
   
   ## Context
   [When/where this applies]
   
   ## Pattern/Solution
   [The actual pattern or solution]
   
   ## Example
   ```python
   # Code example
   ```
   
   ## References
   - Related to: [component/file]
   - VideoCommentator equivalent: [if applicable]
   EOF
   ```
2. Run ingestion:
   ```bash
   cd dev-knowledge-base
   python ingestion/extract_knowledge.py
   ```
3. Verify it's searchable:
   ```bash
   ./dev-cli ask "[keyword from your addition]"
   ```
4. Update project notes in MongoDB about new knowledge
```

---

## Implementation Templates

### Implementation Plan Step Execution Template
```
Help me implement [component/feature] from the Video Intelligence PRD.

Component: [specific component from PRD]
PRD Section: [section reference]

Pre-execution:
1. Query knowledge base for patterns:
   ```bash
   ./dev-cli ask "How to implement [component]"
   ./dev-cli ask "VideoCommentator [similar feature]"
   ```
2. Check MongoDB schemas:
   - Review relevant models in services/backend/models/
   - Ensure schema alignment with PRD
3. Review old VideoCommentator code:
   - Check path references in CLAUDE.md
   - Look for similar implementations
4. Present plan:
   - Components to create/modify
   - Patterns to follow
   - Potential issues
   - **WAIT for approval**

Implementation:
1. Create service structure following PRD layout
2. Use patterns from knowledge base
3. Implement with:
   - Proper error handling
   - Cost tracking (if provider)
   - Progress updates to MongoDB
   - Celery task patterns (if async)
4. Test locally:
   - Create simple test script
   - Verify MongoDB updates
   - Check logs for errors

Post-implementation:
1. Update project status in MongoDB
2. Document any new patterns discovered
3. Add to knowledge base if significant
4. Report:
   - What was completed
   - Any issues found
   - Next logical step
```

### Multi-Component Implementation Session Template
```
Implement multiple related components from the PRD in sequence.

Components: [list from PRD]

Session plan:
1. Analyze dependencies between components
2. Query knowledge base for all components:
   ```bash
   ./dev-cli ask "Implementation order for [components]"
   ```
3. Check MongoDB models for relationships
4. Create implementation order
5. For each component:
   - Follow single component template
   - Update MongoDB status after each
   - Test integration with previous components
6. Final integration test
7. Update project documentation
```

---

## Feature Implementation

### New Feature Template (Video Intelligence)
```
Implement [feature name] for the Video Intelligence Platform.

Feature: [description]
Phase: [from PRD phases]

Steps:
1. Knowledge base check:
   ```bash
   ./dev-cli ask "[feature] implementation patterns"
   ./dev-cli ask "Similar features in VideoCommentator"
   ```
2. Review PRD requirements:
   - Check feature specifications
   - MongoDB schema requirements
   - Provider integrations needed
3. Design approach:
   - Which services affected
   - New models/schemas needed
   - Celery tasks required
   - API endpoints
4. Implementation:
   - Follow PRD structure
   - Use knowledge base patterns
   - Create services in correct directories
   - Add proper error handling
   - Include cost tracking
5. Testing:
   - Unit tests for service
   - Integration test with MongoDB
   - Local Docker testing
6. Update:
   - MongoDB project status
   - Knowledge base with patterns
   - PRD progress tracking
```

### Provider Integration Template (Video Intelligence)
```
Add new provider integration for [provider name].

Provider: [AWS Rekognition/NVIDIA/OpenAI/etc.]
Service: [chunking/analysis/embedding/etc.]

Pre-implementation:
1. Check existing providers:
   ```bash
   ./dev-cli ask "Provider abstraction pattern"
   ./dev-cli ask "[provider] integration examples"
   ```
2. Review VideoCommentator patterns:
   - Factory pattern from old code
   - Cost tracking implementation
   - Error handling patterns

Implementation:
1. Create provider class:
   ```python
   # services/backend/services/analysis/providers/[provider].py
   from ..base_analyzer import BaseAnalyzer
   
   class [Provider]Analyzer(BaseAnalyzer):
       # Implementation following pattern
   ```
2. Add to provider factory
3. Implement required methods:
   - analyze_chunk()
   - get_capabilities()
   - estimate_cost()
   - handle_errors()
4. Add configuration:
   - Environment variables
   - Cost constants
   - Rate limits
5. Create tests:
   - Mock provider responses
   - Test error handling
   - Verify cost calculation
6. Update:
   - Provider documentation
   - MongoDB status
   - Knowledge base
```

---

## Bug Fixing and Investigation

### Bug Investigation Template (Video Intelligence)
```
Debug issue in [component]: [description]

Symptoms: [what's happening]

Investigation:
1. Check knowledge base for similar issues:
   ```bash
   ./dev-cli ask "Issues with [component]"
   ./dev-cli ask "[error message]"
   ```
2. Review relevant logs:
   - Docker compose logs
   - MongoDB query logs
   - Celery worker logs
3. Check MongoDB data:
   - Processing job status
   - Error messages stored
   - Component states
4. Identify root cause:
   - Compare with PRD specifications
   - Check against VideoCommentator patterns
   - Verify environment setup
5. Fix approach:
   - Minimal change for immediate fix
   - Proper solution if different
   - Add to knowledge base
6. Test fix:
   - Reproduce original issue
   - Verify fix works
   - Check for regressions
7. Update:
   - Add to knowledge base
   - Update project status
   - Document in code
```

---

## Testing

### Test Implementation Template (Video Intelligence)
```
Add tests for [component/service].

Component: [what to test]
Test types: [unit/integration/e2e]

Steps:
1. Review existing test patterns:
   ```bash
   ./dev-cli ask "Testing patterns for [component type]"
   ```
2. Check VideoCommentator test examples:
   - Look for similar component tests
   - Copy test structure
3. Create tests:
   ```python
   # services/backend/tests/test_[component].py
   import pytest
   from ..models import [Model]
   from ..services.[component] import [Service]
   
   class Test[Component]:
       # Tests following patterns
   ```
4. Test coverage:
   - Happy path
   - Error conditions  
   - MongoDB interactions
   - Provider mocking (if applicable)
   - Celery task execution (if async)
5. Run tests:
   ```bash
   cd services/backend
   pytest tests/test_[component].py -v
   ```
6. Update knowledge base with test patterns
```

---

## Documentation

### Documentation Sync Template (Video Intelligence)
```
Update documentation for [component/feature].

Changed: [what was implemented/modified]

Tasks:
1. Update PRD progress:
   - Mark completed items in implementation phases
   - Update component status
2. Create/update technical docs:
   - API documentation (if new endpoints)
   - Service documentation
   - MongoDB schema docs
3. Update knowledge base:
   - New patterns discovered
   - Implementation decisions
   - Lessons learned
4. Sync AI assistant files:
   - Update CLAUDE.md if new patterns
   - Add to PROMPTS.md if new templates needed
5. Verify:
   - All file paths correct
   - Code examples work
   - MongoDB schemas accurate
```

---

## Architecture and Infrastructure

### Architecture Decision Template (Video Intelligence)
```
Propose architecture change: [description]

Current issue: [limitation/problem]
Proposed solution: [change description]

Analysis:
1. Check knowledge base:
   ```bash
   ./dev-cli ask "Architecture patterns for [area]"
   ./dev-cli ask "Scaling [component]"
   ```
2. Review PRD architecture:
   - Two-phase system design
   - MongoDB schema implications
   - Provider abstraction impacts
3. Consider VideoCommentator lessons:
   - What worked/didn't work
   - Scaling issues faced
   - Cost implications
4. Impact analysis:
   - Components affected
   - Migration requirements
   - Performance implications
   - Cost changes
5. Implementation plan:
   - Phased approach
   - Backward compatibility
   - Testing strategy
6. Document decision:
   - Add to knowledge base
   - Update architecture docs
   - Create ADR if significant
```

### MongoDB Schema Update Template
```
Update MongoDB schema for [collection/feature].

Change needed: [description]
Collection: [which collection]

Steps:
1. Review current schema:
   - Check models/[collection].py
   - Verify PRD alignment
2. Check impacts:
   ```bash
   ./dev-cli ask "MongoDB migration patterns"
   ```
3. Update Beanie model:
   - Add new fields with defaults
   - Update validators
   - Maintain backwards compatibility
4. Migration strategy:
   - Create migration script if needed
   - Handle existing documents
   - Update indexes
5. Test thoroughly:
   - Test with existing data
   - Verify new functionality
   - Check performance
6. Update:
   - Schema documentation
   - Knowledge base
   - Project status
```

---

## Deployment and DevOps

### Local Development Setup Template
```
Set up local development environment for [component/full system].

Requirements: [what needs to work]

Steps:
1. Environment check:
   ```bash
   # Check Docker
   docker --version
   docker compose version
   
   # Check Python
   python --version
   source venv/bin/activate
   pip list | grep -E "(beanie|motor|fastapi|celery)"
   
   # Check MongoDB
   docker compose ps mongodb
   ```
2. Knowledge base setup:
   ```bash
   # Test dev-cli
   ./dev-cli ask "Setup requirements"
   ```
3. Initialize MongoDB:
   ```bash
   # Run init script
   python scripts/init_project_status.py
   ```
4. Start services:
   ```bash
   docker compose up -d mongodb redis
   # Start other services as needed
   ```
5. Verify:
   - MongoDB connection works
   - Redis is accessible  
   - Knowledge base queries work
   - Project status readable
```

### Production Deployment Prep Template
```
Prepare [component] for AWS deployment.

Component: [what to deploy]
Service: [ECS service name]

Pre-deployment:
1. Check deployment patterns:
   ```bash
   ./dev-cli ask "AWS deployment checklist"
   ./dev-cli ask "ECS configuration patterns"
   ```
2. Verify:
   - Docker image builds
   - Environment variables documented
   - Secrets in AWS Secrets Manager
   - MongoDB connection string
   - Redis configuration
3. Resource requirements:
   - CPU/Memory from VideoCommentator lessons
   - Auto-scaling configuration
   - Cost estimates
4. Update configurations:
   - ECS task definition
   - Environment variables
   - Health check endpoints
5. Document:
   - Deployment steps
   - Rollback procedure
   - Monitoring setup
```

---

## Quick Commands Reference

```bash
# Virtual environment
source venv/bin/activate

# Knowledge base queries
./dev-cli ask "Your question about implementation"
./dev-cli suggest "component name"

# MongoDB status
python scripts/init_project_status.py

# Local MongoDB access
docker compose exec mongodb mongosh video_intelligence

# Testing
cd services/backend && pytest
cd services/backend && pytest tests/test_specific.py -v

# Docker operations
docker compose up -d mongodb redis
docker compose logs -f [service]
docker compose down

# Common paths
# PRD: /docs/new/video-intelligence-prd.md
# Models: /services/backend/models/
# Knowledge base: /dev-knowledge-base/
# Old repo: /Users/filip/Documents/Source/VideoCommentator-MonoRepo
```

---

## Best Practices

1. **Always query knowledge base first** - Don't reinvent patterns
2. **Update MongoDB status regularly** - Track progress systematically
3. **Follow PRD structure** - Maintain consistency with design
4. **Document patterns** - Add to knowledge base for future
5. **Test locally first** - Use Docker environment
6. **Reference old code** - Learn from VideoCommentator experience

---

## Adding New Templates

When adding templates for new workflows:
1. Follow existing format
2. Include knowledge base queries
3. Add MongoDB status updates
4. Reference PRD sections
5. Update template shortcuts
6. Test the template workflow