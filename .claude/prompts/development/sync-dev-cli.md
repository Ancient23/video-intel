# Sync Dev CLI and Scripts

Ensure dev-cli and all related scripts are synchronized with project changes, including new prompts, scripts, commands, and documentation updates.

## Instructions

1. **Scan for New Prompts**
   ```bash
   # List all prompt files
   find .claude/prompts -name "*.md" -type f | sort
   
   # Check which prompts are in scripts/prompt.py
   grep -E "\"[^\"]+\": {" scripts/prompt.py | grep -oE "\"[^\"]+\"" | head -n -1 | sort
   
   # Compare to find missing prompts
   ```

2. **Check Documentation for New Commands**
   Review all documentation files for command references:
   ```bash
   # Search for dev-cli command patterns
   grep -r "./dev-cli" docs/ README.md CLAUDE.md .claude/
   grep -r "dev-cli " docs/ README.md CLAUDE.md .claude/
   
   # Search for script execution patterns
   grep -r "python scripts/" docs/ README.md CLAUDE.md .claude/
   grep -r "python tools/" docs/ README.md CLAUDE.md .claude/
   
   # Look for bash script references
   grep -r "\./scripts/" docs/ README.md CLAUDE.md .claude/
   ```

3. **Scan for New Scripts**
   ```bash
   # List all Python scripts
   find scripts/ tools/ -name "*.py" -type f | sort
   
   # List all bash scripts
   find scripts/ -name "*.sh" -type f | sort
   
   # Check if they're documented or integrated
   ```

4. **Review Key Documentation Files**
   Read and check for command patterns in:
   - `README.md` - Main project documentation
   - `CLAUDE.md` - Claude-specific instructions
   - `.claude/README.md` - Prompt system documentation
   - `docs/new/video-intelligence-prd.md` - PRD commands
   - `dev-knowledge-base/README.md` - Knowledge base commands
   - Any other `.md` files with setup/usage instructions

5. **Check Environment Variables**
   ```bash
   # Review .env.example for new variables
   cat .env.example
   
   # Check if dev-cli handles all env vars
   grep -n "os.environ" scripts/*.py tools/*.py
   
   # Verify all required vars are documented
   ```

6. **Verify Directory Structure**
   ```bash
   # Check for new directories that might need commands
   find . -type d -name "__pycache__" -prune -o -type d -print | grep -E "^./[^/]+/?$"
   
   # Look for directories with scripts or tools
   find . -type d -name "__pycache__" -prune -o -type d -exec test -e {}/*.py \; -print
   ```

7. **Update dev-cli if Needed**
   For each missing command found:
   ```python
   # Add to dev-cli command registry
   commands = {
       "existing_cmd": existing_function,
       "new_cmd": new_function,  # Add this
   }
   
   # Implement the function
   def new_function(args):
       """Description of what the command does"""
       # Implementation
   ```

8. **Update prompt.py Registry**
   For each missing prompt:
   ```python
   "prompt-name": {
       "file": "category/prompt-name.md",
       "description": "What this prompt does",
       "category": "category-name"
   },
   ```

9. **Synchronize Help Text**
   Ensure all help text is current:
   - dev-cli --help should list all commands
   - prompt.py help should show all actions
   - Individual command help should be accurate

10. **Create Missing Integrations**
    If documentation references commands that don't exist:
    - Create the missing script
    - Add integration to dev-cli
    - Update help documentation
    - Test the new command

## Checklist

- [ ] All .claude/prompts/*.md files are in prompt.py
- [ ] All documented dev-cli commands exist and work
- [ ] All python scripts/ have dev-cli integration if needed
- [ ] All bash scripts are documented and accessible
- [ ] Environment variables are fully documented
- [ ] Help text reflects current functionality
- [ ] No orphaned scripts without documentation
- [ ] No documented commands without implementation

## Common Patterns to Look For

### In Documentation
- `./dev-cli [command]` - Should have matching command
- `python scripts/[script].py` - Should be integrated or documented
- `Execute the following:` - Often followed by commands
- `Run this command:` - Check if automated
- Setup instructions - Should be in dev-cli

### In Code
- New Python files in scripts/ or tools/
- New bash scripts needing integration
- New directories with tooling
- Config files suggesting commands

## Update Locations

When adding new commands, update:
1. `dev-cli` or relevant script
2. `scripts/prompt.py` for new prompts
3. Help text in the script
4. `README.md` with usage examples
5. `CLAUDE.md` if it affects Claude usage

## Validation

After updates, verify:
```bash
# Test all dev-cli commands
./dev-cli --help
./dev-cli test  # if available

# Test prompt system
python scripts/prompt.py list
python scripts/prompt.py help

# Run any new commands
./dev-cli [new_command] --help
```

## Example Findings and Fixes

### Missing Prompt
```bash
# Found: .claude/prompts/workflows/review-code.md
# Missing from: scripts/prompt.py

# Fix: Add to PROMPT_METADATA in prompt.py
"review-code": {
    "file": "workflows/review-code.md",
    "description": "Code review workflow",
    "category": "workflows"
},
```

### Documented but Missing Command
```bash
# Found in README: ./dev-cli analyze-performance
# Missing from: dev-cli

# Fix: Add command implementation
def analyze_performance(args):
    """Analyze system performance metrics"""
    # Implementation here
    
# Add to command registry
commands["analyze-performance"] = analyze_performance
```