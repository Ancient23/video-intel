# Implement Next Task

Execute the implementation plan from the next-task report, track technical debt, and update project status including PRD tracking.

## Instructions

1. **Read the Next Task Plan & Source**
   - Review the output from `project-management/next-task` prompt
   - Identify which section of the PRD the task came from
   - Check PRD implementation status tracking for that section
   - Note any potential technical debt or improvements

2. **Verify PRD Alignment**
   ```bash
   # Check the PRD section that next-task referenced
   # Look for implementation status markers in docs/new/video-intelligence-prd.md
   
   # Common PRD sections to check:
   # - Phase 1: Foundation (MongoDB, Redis, Celery setup)
   # - Phase 2: Ingestion Pipeline (chunking, analysis, knowledge extraction)
   # - Phase 3: Runtime & API (retrieval, conversational AI)
   # - Implementation Checklist sections
   ```

3. **Create Implementation Plan**
   ```bash
   # First, check current technical debt
   python scripts/prompt.py exec debt-check
   
   # Create todo list for implementation including:
   # - Main tasks from next-task output
   # - PRD checklist items for this component
   # - Related technical debt to address
   # - Testing requirements from PRD
   # - Documentation updates needed
   ```

4. **Implementation Process**
   - Start with any blocking technical debt items
   - Implement main functionality following the plan
   - Ensure implementation matches PRD specifications
   - Add comprehensive error handling and logging
   - Write tests alongside implementation
   - Document any deviations from PRD

5. **Update PRD Implementation Status**
   After implementing each component:
   - Mark completed items in PRD checklists
   - Update implementation status sections
   - Note any architectural decisions or changes
   - Document lessons learned
   
   Example PRD update:
   ```markdown
   ### Phase 2: Ingestion Pipeline
   #### Video Chunking Service ✅
   - [x] Implement shot detection with AWS Rekognition
   - [x] Create chunking algorithms
   - [x] Store chunks with metadata in MongoDB
   - Implementation Notes: Added caching layer for performance
   ```

6. **Technical Debt Tracking**
   During implementation, watch for and document:
   - Code that needs refactoring but works
   - Missing tests or documentation
   - Performance optimizations needed
   - Security improvements required
   - Dependency updates needed
   - Architecture improvements
   - Deviations from PRD that need revisiting
   
   For each item found:
   ```bash
   python scripts/prompt.py exec debt-add --component "[component]" --description "[issue]" --impact "[low/medium/high]"
   ```

7. **Quality Checks**
   - Run linting: `ruff check services/backend/`
   - Run type checking: `mypy services/backend/`
   - Run tests: `pytest services/backend/tests/`
   - Check test coverage: `pytest --cov=services/backend`
   - Verify implementation matches PRD specifications

8. **Update Project Status**
   After implementation:
   ```bash
   # Update MongoDB project status
   python scripts/prompt.py exec status-update
   
   # Update PRD if needed
   # - Mark completed checklist items
   # - Add implementation notes
   # - Update phase completion percentages
   ```

## PRD Section Mapping

When next-task references these areas, check corresponding PRD sections:

- **Infrastructure Setup** → PRD Section 3.1 (MongoDB, Redis, Celery)
- **Video Processing** → PRD Section 3.2 (Chunking Service)
- **Analysis Pipeline** → PRD Section 3.3 (Provider Integration)
- **Knowledge Extraction** → PRD Section 3.4 (Graph Construction)
- **API Development** → PRD Section 4 (REST API Design)
- **Testing** → PRD Section 7 (Testing Strategy)

## Checklist

- [ ] Reviewed next-task output and identified PRD source section
- [ ] Checked PRD implementation status for that section
- [ ] Created comprehensive todo list aligned with PRD
- [ ] Checked existing technical debt
- [ ] Implemented all required functionality per PRD specs
- [ ] Added proper error handling and logging
- [ ] Wrote unit and integration tests
- [ ] Ran all quality checks (lint, type, test)
- [ ] Documented new technical debt items
- [ ] Updated PRD with completion status and notes
- [ ] Updated project status in MongoDB
- [ ] Verified no unfinished todos remain

## Common Patterns to Watch For

1. **PRD Deviations**: Implementation differs from original design
2. **Missing Error Handling**: Any try/except blocks without proper logging
3. **Hard-coded Values**: Configuration that should be in environment variables
4. **Missing Tests**: New functions without corresponding test coverage
5. **Performance Issues**: Unoptimized database queries or API calls
6. **Security Concerns**: Exposed credentials, missing validation
7. **Documentation Gaps**: Complex logic without explanations

## Post-Implementation

1. Review all completed todos
2. Verify PRD checklist items are updated
3. Check for any partially completed work
4. Document lessons learned in knowledge base
5. Plan next iteration if needed
6. Ensure PRD reflects actual implementation state