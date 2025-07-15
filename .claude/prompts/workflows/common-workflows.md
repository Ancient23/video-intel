# Common Development Workflows

## Description
Multi-step workflows for common development tasks in the Video Intelligence Platform.

## Workflow 1: Start New Feature

### When to Use
Beginning implementation of a new feature or component.

### Steps
```bash
# 1. Check current status
./dev-cli prompt status-check

# 2. Query for patterns
./dev-cli prompt knowledge-query
# Ask: "How to implement [feature]"
# Ask: "VideoCommentator [similar feature]"

# 3. Check technical debt
./dev-cli prompt debt-check
# Look for related blockers

# 4. Create implementation plan
./dev-cli prompt impl-plan

# 5. Implement feature
./dev-cli prompt feature

# 6. Add tests
./dev-cli prompt test

# 7. Update status
./dev-cli prompt status-update

# 8. Document patterns
./dev-cli prompt knowledge-add
```

## Workflow 2: Fix High-Priority Bug

### When to Use
Critical bug affecting functionality.

### Steps
```bash
# 1. Investigate issue
./dev-cli prompt bug

# 2. Query for similar issues
./dev-cli prompt knowledge-query
# Ask: "Issues with [component]"
# Ask: "[Error message]"

# 3. Implement fix
# Follow bug prompt guidance

# 4. Add regression test
./dev-cli prompt test --type regression

# 5. Update technical debt
./dev-cli prompt debt-resolve

# 6. Document solution
./dev-cli prompt knowledge-add --type solution
```

## Workflow 3: Resolve Technical Debt

### When to Use
Dedicated time for debt reduction.

### Steps
```bash
# 1. Review technical debt
./dev-cli prompt debt-check

# 2. Select item to fix
# Prioritize blockers or quick wins

# 3. Query for solutions
./dev-cli prompt knowledge-query
# Ask: "How to implement [proper solution]"

# 4. Implement fix
./dev-cli prompt debt-resolve

# 5. Add tests
./dev-cli prompt test

# 6. Update status
./dev-cli prompt status-update
```

## Workflow 4: Add Provider Integration

### When to Use
Integrating new AI/ML provider.

### Steps
```bash
# 1. Check provider patterns
./dev-cli prompt knowledge-query
# Ask: "Provider abstraction pattern"
# Ask: "Provider factory pattern"

# 2. Review existing providers
# Check services/backend/services/analysis/providers/

# 3. Implement provider
./dev-cli prompt feature-provider

# 4. Add to factory
# Update provider factory

# 5. Create tests
./dev-cli prompt test --component provider

# 6. Update documentation
./dev-cli prompt knowledge-add --type integration

# 7. Update project status
./dev-cli prompt status-update
```

## Workflow 5: Performance Optimization

### When to Use
Addressing performance issues.

### Steps
```bash
# 1. Profile the issue
# Use memory_monitor, logs, metrics

# 2. Query optimization patterns
./dev-cli prompt knowledge-query
# Ask: "Optimize [operation]"
# Ask: "Performance [component]"

# 3. Check VideoCommentator solutions
./dev-cli prompt knowledge-query
# Ask: "VideoCommentator performance optimizations"

# 4. Implement optimization
# Follow patterns found

# 5. Measure improvement
# Before/after benchmarks

# 6. Document approach
./dev-cli prompt knowledge-add --type performance

# 7. Update if partial fix
./dev-cli prompt debt-add
```

## Workflow 6: Weekly Maintenance

### When to Use
Regular maintenance and progress tracking.

### Steps
```bash
# Monday: Review and Plan
./dev-cli prompt status-check
./dev-cli prompt debt-check
./dev-cli prompt next-task

# Wednesday: Mid-week Check
./dev-cli prompt status-check
# Adjust priorities if needed

# Friday: Update and Document
./dev-cli prompt status-update
./dev-cli prompt knowledge-add  # Any new patterns
# Generate weekly report

# Ongoing: As You Work
# - Add technical debt when found
# - Document solutions
# - Update status after major completions
```

## Workflow 7: Pre-Release Checklist

### When to Use
Preparing for deployment or release.

### Steps
```bash
# 1. Check all tests pass
pytest services/backend/tests/

# 2. Review technical debt
./dev-cli prompt debt-check
# Ensure no CRITICAL items

# 3. Update documentation
# - API docs
# - README
# - Deployment guide

# 4. Performance check
# Run load tests
# Check memory usage

# 5. Security review
# Check for exposed secrets
# Review authentication
# Verify CORS settings

# 6. Final status update
./dev-cli prompt status-update
```

## Workflow 8: Onboarding New Developer

### When to Use
Getting new team member up to speed.

### Steps
```bash
# Day 1: Environment Setup
# Follow DEVELOPER_ONBOARDING.md

# Day 2: Understand Project
./dev-cli prompt status-check
./dev-cli prompt debt-check
# Review PRD

# Day 3: First Task
./dev-cli prompt next-task
# Find a LOW priority debt item
./dev-cli prompt debt-resolve

# Week 1: Learn Patterns
./dev-cli prompt knowledge-query
# Explore different components

# Ongoing: Contribute
# Follow feature workflow
# Document learnings
```

## Workflow Combinations

### Investigation + Implementation
```bash
# Research phase
./dev-cli prompt knowledge-query
./dev-cli prompt status-check

# Planning phase
./dev-cli prompt impl-plan

# Implementation phase
./dev-cli prompt feature
./dev-cli prompt test

# Completion phase
./dev-cli prompt status-update
./dev-cli prompt knowledge-add
```

### Debt Reduction Sprint
```bash
# Start of sprint
./dev-cli prompt debt-check > debt_start.txt

# Daily
./dev-cli prompt debt-resolve  # Pick one
./dev-cli prompt test          # Add tests
./dev-cli prompt knowledge-add  # Document

# End of sprint
./dev-cli prompt debt-check > debt_end.txt
# Compare progress
```

## Best Practices

1. **Always Start with Status**: Know where you are
2. **Query Before Implementing**: Use existing knowledge
3. **Document After Completing**: Share learnings
4. **Test Everything**: Maintain quality
5. **Track Progress**: Update status regularly

## Quick Commands

```bash
# Most common workflow - implement feature
./dev-cli workflow new-feature [feature-name]

# Fix bug workflow
./dev-cli workflow fix-bug [component]

# Debt reduction workflow
./dev-cli workflow reduce-debt

# Weekly maintenance
./dev-cli workflow weekly-review
```

## Related Prompts
- All individual prompts can be combined into workflows
- Create custom workflows for your team's needs
- Document new workflows in knowledge base