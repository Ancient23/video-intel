# Implement Targeted Feature

Implement a specific feature or enhancement to any component while ensuring all documentation and tracking systems are updated.

## Usage

```bash
python scripts/prompt.py exec implement-targeted
```

Then specify:
- Target: script name, component, API endpoint, service, etc.
- Feature: what you want to implement or enhance

## Instructions

1. **Gather Feature Details**
   - Target location (file, component, service, API endpoint)
   - Feature description and requirements
   - Expected behavior and acceptance criteria

2. **Check Existing Documentation**
   ```bash
   # Check if this feature is mentioned in PRD
   grep -n "[feature_name]" docs/new/video-intelligence-prd.md
   
   # Check technical debt for related issues
   python scripts/prompt.py exec debt-check
   
   # Check current project status
   python scripts/prompt.py exec status-check
   ```

3. **Analyze Impact**
   - Review the target component's current implementation
   - Check for existing patterns and conventions
   - Identify dependencies and integration points
   - Assess potential technical debt

4. **Implementation Plan**
   Create todo list including:
   - [ ] Review target component and dependencies
   - [ ] Check PRD for related specifications
   - [ ] Review technical debt for blockers
   - [ ] Implement core functionality
   - [ ] Add error handling and logging
   - [ ] Write comprehensive tests
   - [ ] Update documentation
   - [ ] Update tracking systems

5. **Pre-Implementation Checks**
   ```python
   # Check if feature exists in PRD
   if feature_in_prd:
       # Follow PRD specifications
       # Note any deviations needed
   else:
       # Document new feature addition
       # Update PRD with new section
   ```

6. **Implementation Process**
   - Follow existing code patterns and conventions
   - Implement with comprehensive error handling
   - Add detailed logging for debugging
   - Include inline documentation for complex logic
   - Write tests alongside implementation

7. **Quality Assurance**
   ```bash
   # Run linting
   ruff check [target_file]
   
   # Type checking
   mypy [target_file]
   
   # Run tests
   pytest tests/[relevant_tests] -v
   
   # Check test coverage
   pytest --cov=[module] tests/
   ```

8. **Documentation Updates**
   
   **If feature IS in PRD:**
   - Update implementation status
   - Mark completed checklist items
   - Add implementation notes
   - Document any deviations
   
   **If feature IS NOT in PRD:**
   - Add new section describing the feature
   - Include rationale and design decisions
   - Document API changes or new endpoints
   - Update relevant architecture sections
   
   Example PRD addition:
   ```markdown
   ### [Component Name] - [Feature Name]
   
   **Added**: [Date]
   **Status**: ✅ Implemented
   
   #### Description
   [Feature description and purpose]
   
   #### Implementation Details
   - Technology: [e.g., FastAPI, Celery, etc.]
   - Location: `[file path]`
   - Key Functions: `[function names]`
   
   #### API Changes (if applicable)
   - Endpoint: `[method] /api/v1/[path]`
   - Request: [schema]
   - Response: [schema]
   
   #### Testing
   - Unit tests: `tests/[test_file]`
   - Integration tests: `tests/integration/[test_file]`
   ```

9. **Technical Debt Tracking**
   ```bash
   # Add any new technical debt discovered
   python scripts/prompt.py exec debt-add \
     --component "[component]" \
     --description "[issue]" \
     --impact "[low/medium/high]"
   
   # Resolve any addressed debt
   python scripts/prompt.py exec debt-resolve --id [debt_id]
   ```

10. **Update Project Status**
    ```bash
    # Update MongoDB with progress
    python scripts/prompt.py exec status-update
    ```
    
    Include in status update:
    - Feature implemented
    - Files modified
    - Tests added
    - Documentation updated
    - Any technical debt changes

## Tracking Template

Use this template for features not in PRD:

```markdown
## Feature: [Name]
- **Date**: [date]
- **Target**: [component/file]
- **Description**: [what was implemented]
- **Rationale**: [why it was needed]
- **Impact**: [what it affects]
- **Tests**: [test files added]
- **Technical Debt**: [any debt created or resolved]
```

## Common Patterns

### API Endpoint Addition
1. Add route to appropriate router
2. Create request/response schemas
3. Implement service logic
4. Add comprehensive tests
5. Update API documentation
6. Update PRD API section

### Service Enhancement
1. Review existing service pattern
2. Add new methods following conventions
3. Update interfaces if needed
4. Add unit tests
5. Update integration tests
6. Document in PRD services section

### Worker Task Addition
1. Follow Celery task patterns
2. Implement with proper error handling
3. Add retry logic
4. Create tests with mocking
5. Update PRD worker section
6. Document in task registry

## Checklist

- [ ] Feature requirements clearly defined
- [ ] Checked PRD, technical debt, and status
- [ ] Implementation follows existing patterns
- [ ] Comprehensive error handling added
- [ ] Tests written and passing
- [ ] Documentation updated (code + PRD)
- [ ] Technical debt tracked
- [ ] Project status updated
- [ ] No unfinished todos remain

## Post-Implementation

1. Verify all tests pass
2. Confirm documentation is complete
3. Review code for optimization opportunities
4. Check for any security concerns
5. Ensure monitoring/logging is adequate