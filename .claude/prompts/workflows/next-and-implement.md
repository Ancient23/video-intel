# Next Task and Implementation Workflow

Identifies the next task from the PRD and project status, presents the plan for approval, then executes implementation with technical debt tracking.

## Workflow Steps

### Step 1: Identify Next Task
```bash
# Run the next-task analysis
python scripts/prompt.py exec next-task
```

### Step 2: Review and Approve
After reviewing the next-task output:

1. **Review the proposed task plan**
   - Verify it aligns with current project phase
   - Check dependencies are met
   - Confirm technical approach makes sense
   - Review time estimates

2. **Decision Point**
   ```
   The plan above has been generated from the PRD and current project status.
   
   Would you like to:
   a) Proceed with implementation as planned
   b) Modify the plan (specify changes)
   c) Choose a different task
   d) Skip for now
   
   Please respond with your choice and any modifications needed.
   ```

### Step 3: Execute Implementation
If approved, proceed with:
```bash
# Execute the implementation with debt tracking
python scripts/prompt.py exec implement-next-task
```

## Automated Workflow Script

For a more streamlined experience, you can use:
```bash
# This will run next-task, show the plan, and wait for approval
python scripts/prompt.py workflow next-and-implement
```

## Key Checkpoints

1. **Pre-Implementation Review**
   - [ ] Task aligns with current project phase
   - [ ] Dependencies are available
   - [ ] Technical approach is sound
   - [ ] Time estimate is reasonable
   - [ ] No blocking technical debt

2. **Post-Implementation Verification**
   - [ ] All planned features implemented
   - [ ] Tests written and passing
   - [ ] Technical debt documented
   - [ ] PRD updated with progress
   - [ ] Project status updated

## Approval Templates

### Full Approval
```
Approved. Please proceed with the implementation as planned.
```

### Conditional Approval
```
Approved with modifications:
- [specific change 1]
- [specific change 2]
Please update the plan and then proceed.
```

### Deferral
```
Let's defer this task because [reason].
Instead, please analyze [alternative task or area].
```

## Benefits of This Workflow

1. **Visibility**: See what will be done before it happens
2. **Control**: Approve or modify plans before execution
3. **Tracking**: Automatic technical debt and progress tracking
4. **Alignment**: Ensures work matches PRD and project goals
5. **Quality**: Built-in testing and documentation requirements

## Example Usage

```
User: Let's work on the next task