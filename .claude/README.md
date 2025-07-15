# AI Assistant Prompts

This directory contains structured prompts for AI coding assistants (Claude Code, GitHub Copilot, Cursor, etc.) working on the Video Intelligence Platform.

## Directory Structure

```
.claude/
└── prompts/
    ├── project-management/    # Status tracking and updates
    │   ├── status-check.md
    │   ├── status-update.md
    │   └── next-task.md
    ├── technical-debt/       # Debt management prompts
    │   ├── debt-check.md
    │   ├── debt-add.md
    │   └── debt-resolve.md
    ├── development/          # Implementation prompts
    │   ├── impl-plan.md
    │   ├── impl-multi.md
    │   ├── feature.md
    │   ├── feature-provider.md
    │   ├── bug.md
    │   ├── test.md
    │   └── doc-sync.md
    ├── knowledge-base/       # Knowledge base queries
    │   ├── knowledge-query.md
    │   └── knowledge-add.md
    ├── workflows/            # Multi-step workflows
    │   └── common-workflows.md
    ├── architecture/         # Design and schema decisions
    │   ├── arch-decision.md
    │   └── schema-update.md
    └── infrastructure/       # Setup and deployment
        ├── local-setup.md
        └── deploy-prep.md
```

## How to Use These Prompts

### For AI Assistants

1. **Direct Reference**: 
   ```
   Use the prompt from .claude/prompts/project-management/status-check.md
   ```

2. **By Category**:
   ```
   Apply the technical debt check prompt from .claude/prompts/technical-debt/
   ```

3. **Execution**:
   ```
   Execute the status check workflow: python scripts/prompt.py exec status-check
   ```

### For Developers

1. **List Available Prompts**:
   ```bash
   python scripts/prompt.py list
   
   # List by category
   python scripts/prompt.py list --category development
   
   # Export as JSON
   python scripts/prompt.py export > prompts.json
   ```

2. **View a Prompt**:
   ```bash
   python scripts/prompt.py show status-check
   
   # Show with category
   python scripts/prompt.py show impl-plan
   ```

3. **Execute a Prompt**:
   ```bash
   python scripts/prompt.py exec status-check
   
   # Note: Only works with prompts containing bash commands
   # Interactive prompts require terminal input
   ```

## Prompt Categories

### Project Management
- `status-check` - Check current project status and progress
- `status-update` - Update project status after completing work
- `next-task` - Determine next implementation priority

### Technical Debt
- `debt-check` - Review current technical debt
- `debt-add` - Add new technical debt item
- `debt-resolve` - Mark debt as resolved

### Development
- `impl-plan` - Plan implementation approach
- `impl-multi` - Multi-component implementation
- `feature` - Implement new feature
- `feature-provider` - Add provider integration
- `bug` - Investigate and fix bugs
- `test` - Add test coverage
- `doc-sync` - Sync documentation

### Knowledge Base
- `knowledge-query` - Query development patterns
- `knowledge-add` - Add new knowledge

### Workflows
- `common-workflows` - Multi-step development workflows

### Architecture
- `arch-decision` - Architecture decision template
- `schema-update` - MongoDB schema updates

### Infrastructure
- `local-setup` - Local development setup
- `deploy-prep` - Production deployment prep

## Prompt Format

Each prompt file follows this structure:

```markdown
# Prompt Name

## Description
Brief description of what this prompt does

## When to Use
- Scenario 1
- Scenario 2

## Prerequisites
- Required tools or setup
- Environment variables

## Steps
1. Step-by-step instructions
2. With specific commands
3. Expected outputs

## Example Usage
```

## Best Practices

1. **Always Check Status First**: Run status-check before starting work
2. **Chain Prompts**: Combine prompts for complex tasks
3. **Update After Work**: Use status-update to track progress
4. **Document Learnings**: Add new patterns to knowledge base

## Adding New Prompts

1. Create new `.md` file in appropriate category
2. Follow the standard format above
3. Update prompt loader with new prompt
4. Test execution with `prompt.py`
5. Document in this README

## Integration with Claude Code

When using Claude Code, you can reference prompts in several ways:

1. **Ask to use a specific prompt**:
   ```
   Use the status-check prompt to show me the current project state
   ```

2. **Combine multiple prompts**:
   ```
   First use knowledge-query to check patterns, then use feature to implement
   ```

3. **Execute and analyze**:
   ```
   Execute the debt-check prompt and analyze which items to fix first
   ```

## Troubleshooting

### Prompt Not Found
- Check prompt name spelling
- Verify file exists in correct directory
- Run `python scripts/prompt.py list` to see available prompts

### Execution Errors
- Ensure virtual environment is activated
- Check MongoDB is running for status prompts
- Verify required tools are installed

### Permission Issues
- Make scripts executable: `chmod +x scripts/prompt.py`
- Check file permissions in .claude directory