# Document Templates Reference

This file provides guidance on where to find document templates.

## Primary Templates

The complete templates are maintained in the project at:
```
docs/static/development/context-engineering-templates.md
```

**Always read this file when creating new contexts** to use the latest templates.

## Available Templates

The templates file includes complete templates for:

1. **requirements.md** - Requirements documentation
2. **architecture-changes.md** - Architecture changes
3. **feature-spec.md** - Feature specifications
4. **plan.md** - Implementation plan
5. **test-plan.md** - Test plan
6. **SUMMARY.md** - Archive summary (generated when archiving)

## Template Usage

When initializing a new context, the `init_context.py` script automatically creates all required documents using these templates. The templates include:

- Structured sections with clear headings
- Placeholder text in [brackets]
- Checklists for tracking progress
- Standard formatting for consistency

## Customization

Templates can be customized for specific project needs by:
1. Editing the source templates in `docs/static/development/context-engineering-templates.md`
2. Modifying the `init_context.py` script to use custom templates
3. Adding project-specific sections or requirements

## Quick Reference

### requirements.md Structure
- Background
- Goals
- Functional Requirements
- Non-functional Requirements
- Constraints
- Acceptance Criteria

### architecture-changes.md Structure
- Change Overview
- Affected Components
- New Components
- Data Model Changes
- API Changes
- Architecture Decisions (ADRs)
- Static Docs to Update

### feature-spec.md Structure
- Feature Overview
- User Interface
- Business Logic
- Data Flow
- Error Handling
- Edge Cases

### plan.md Structure
- Phase Division
- Dependencies
- Risk Assessment

### test-plan.md Structure
- Test Strategy
- Test Cases (Functional, Performance, Security)
- Test Environment
- Test Data

### SUMMARY.md Structure (Archive)
- Basic Information
- Completion Status
- Key Decisions
- Problems and Solutions
- Test Results
- Updated Static Docs
- Follow-up Work
- Experience Summary
