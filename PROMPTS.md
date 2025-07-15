# PROMPTS.md

This file provides a reference guide for using the reusable prompt templates for the Video Intelligence Platform project.

⚠️ **IMPORTANT**: Prompt templates have been moved to individual files in `.claude/prompts/` directory for better organization.

## Quick Reference Guide

### How to Use Prompts

**Preferred Method:** Use the prompt loader script:

```bash
# List all available prompts
python scripts/prompt.py list

# List prompts by category
python scripts/prompt.py list --category development

# Show a specific prompt
python scripts/prompt.py show impl-plan

# Execute a prompt (runs embedded commands)
python scripts/prompt.py exec status-check
```

### Prompt Categories

- **project-management**: Status tracking, task management
- **technical-debt**: Debt tracking and resolution
- **development**: Implementation, features, bugs, testing
- **knowledge-base**: Query and update knowledge
- **workflows**: Multi-step processes
- **architecture**: Design decisions, schema updates
- **infrastructure**: Setup and deployment

### Template Shortcuts

| Shortcut | Description | Category |
|----------|-------------|----------|
| `status-check` | Check current project status | project-management |
| `status-update` | Update project status after work | project-management |
| `next-task` | Get next implementation task | project-management |
| `debt-check` | Review technical debt | technical-debt |
| `debt-add` | Add technical debt item | technical-debt |
| `debt-resolve` | Resolve technical debt | technical-debt |
| `impl-plan` | Plan implementation approach | development |
| `impl-multi` | Multi-component implementation | development |
| `feature` | Implement new feature | development |
| `feature-provider` | Add provider integration | development |
| `bug` | Investigate and fix bug | development |
| `test` | Add test coverage | development |
| `doc-sync` | Sync documentation | development |
| `knowledge-query` | Query development patterns | knowledge-base |
| `knowledge-add` | Add new knowledge | knowledge-base |
| `common-workflows` | Multi-step workflows | workflows |
| `arch-decision` | Architecture decisions | architecture |
| `schema-update` | MongoDB schema updates | architecture |
| `local-setup` | Local development setup | infrastructure |
| `deploy-prep` | Production deployment prep | infrastructure |

### Example Usage

#### For AI Assistants:
```
Use the impl-plan prompt for implementing the video chunking service.
```

#### For Command Line:
```bash
# Check project status
python scripts/prompt.py exec status-check

# Plan implementation
python scripts/prompt.py show impl-plan

# Show technical debt
python scripts/prompt.py exec debt-check
```

#### Combining Prompts:
```
For this task, combine:
1. Start with knowledge-query to check existing patterns
2. Use feature for the main implementation
3. Finish with status-update to track progress
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

## Quick Commands Reference

```bash
# Virtual environment
source venv/bin/activate

# Prompt commands
python scripts/prompt.py list                    # List all prompts
python scripts/prompt.py show [prompt-name]     # Show prompt content
python scripts/prompt.py exec [prompt-name]     # Execute prompt

# Knowledge base queries
./dev-cli ask "Your question about implementation"
./dev-cli suggest "component name"

# MongoDB status
python scripts/init_project_status.py
python scripts/init_technical_debt.py

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
# Prompts: /.claude/prompts/
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

## Adding New Prompts

When adding prompts for new workflows:
1. Create a new file in `.claude/prompts/[category]/[name].md`
2. Follow existing template format
3. Include knowledge base queries
4. Add MongoDB status updates
5. Reference PRD sections
6. Update `scripts/prompt.py` with metadata
7. Test the prompt workflow

---

## Directory Structure

```
.claude/prompts/
├── project-management/
│   ├── status-check.md
│   ├── status-update.md
│   └── next-task.md
├── technical-debt/
│   ├── debt-check.md
│   ├── debt-add.md
│   └── debt-resolve.md
├── development/
│   ├── impl-plan.md
│   ├── impl-multi.md
│   ├── feature.md
│   ├── feature-provider.md
│   ├── bug.md
│   ├── test.md
│   └── doc-sync.md
├── knowledge-base/
│   ├── knowledge-query.md
│   └── knowledge-add.md
├── workflows/
│   └── common-workflows.md
├── architecture/
│   ├── arch-decision.md
│   └── schema-update.md
└── infrastructure/
    ├── local-setup.md
    └── deploy-prep.md
```