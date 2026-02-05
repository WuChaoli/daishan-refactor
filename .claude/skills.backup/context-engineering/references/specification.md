# Context Engineering Specification Reference

This file provides guidance on where to find the complete context engineering specification.

## Primary Specification

The complete specification is maintained in the project at:
```
docs/static/development/context-engineering-spec.md
```

**Always read this file before working with contexts** to ensure you're following the latest standards.

## Key Concepts

### Directory Structure

```
project/
├── docs/
│   ├── static/                    # Static docs (long-term maintenance)
│   │   ├── architecture/
│   │   ├── user-journey/
│   │   ├── data-flow/
│   │   └── api/
│   │
│   └── contexts/                  # Development contexts (by time+feature)
│       ├── .contexts-index.json  # Context index
│       └── YYYY-MM-DD_feature-name/
│           ├── .context.json     # Metadata
│           ├── requirements.md
│           ├── architecture-changes.md
│           ├── feature-spec.md
│           ├── plan.md
│           ├── todos.md
│           └── test-plan.md
```

### Document Types

**Static Documents** (`docs/static/`):
- Organized by functional module
- Long-term maintenance
- Categories: architecture/, user-journey/, data-flow/, api/

**Dynamic Documents** (`docs/contexts/[contextId]/`):
- Organized by time + feature
- Supports parallel development
- Standard files: requirements.md, architecture-changes.md, feature-spec.md, plan.md, todos.md, test-plan.md

### Metadata Format

**`.context.json`** - Context metadata:
```json
{
  "contextId": "2026-01-20_user-authentication",
  "status": "in_progress",
  "createdAt": "2026-01-20T10:00:00Z",
  "updatedAt": "2026-01-20T15:30:00Z",
  "completedAt": null,
  "title": "用户认证功能",
  "description": "实现基于 JWT 的用户认证系统",
  "assignee": "developer-name",
  "gitBranch": "feature/user-auth",
  "documents": { ... },
  "staticDocsUpdated": []
}
```

**`.contexts-index.json`** - Global index:
```json
{
  "activeContexts": [ ... ],
  "archivedContexts": [ ... ]
}
```

## Best Practices

1. **Always check current context** - Read `.contexts-index.json` to confirm active contexts
2. **Update metadata promptly** - Update `updatedAt` after modifying documents
3. **Record static doc changes** - Track all changes in `staticDocsUpdated`
4. **Keep docs in sync** - Update both dynamic and static docs for architecture changes
5. **Complete archiving** - Ensure complete SUMMARY.md when archiving
6. **Accumulate experience** - Extract key learnings to project-level CLAUDE.md

## Important Notes

- All contexts unified under `docs/contexts/` directory
- Distinguish active vs archived via `status` field
- Don't move files when archiving, only update status
- Use index file for quick context lookup
- Support multi-developer parallel development
- Timestamps use ISO 8601 format
- contextId uses English lowercase + underscores
