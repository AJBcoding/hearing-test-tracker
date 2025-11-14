# Code Review Plan for Untested Code

**Date:** 2025-11-14
**Author:** Code Review Planning Session
**Status:** Design Complete

## Purpose

Review untested code to identify quality issues across architecture, error handling, and maintainability. Feed findings into improvement design and implementation plans.

## Scope

**Backend (Python/Flask):**
- API routes (`routes.py`, `test_upload.py`)
- Flask application setup (`app.py`)
- Upload endpoints (single and bulk)

**Frontend (TypeScript/React):**
- All 18 source files (zero test coverage)
- Pages: Upload, TestViewer, TestList, TestReviewEdit, Dashboard
- Components: UploadForm, BulkUploadForm, AudiogramChart, AudiogramAnimation, FrequencyTrendChart, TestCalendarHeatmap, ComparisonGrid, AudiogramViewer, Navigation, AppLayout
- API client (`lib/api.ts`)

**Out of Scope:**
- Already-tested OCR modules
- Already-tested database utilities

## Review Approach

### Three Phases

**Phase 1: Quick Scan (1-2 hours)**

Rapidly scan all untested code to identify obvious patterns. Search for missing error handling, security issues, and architectural smells. Create preliminary findings matrix showing severity distribution across flows.

**Phase 2: Severity Categorization (30 minutes)**

Assign severity to findings:
- **High:** Security vulnerabilities, data integrity risks, critical error handling gaps
- **Medium:** Poor architecture, inconsistent patterns, missing validation, UX issues
- **Low:** Code style, minor redundancy, documentation gaps

Select flows for deep analysis based on high and medium severity concentration.

**Phase 3: Deep Dive Analysis (2-4 hours)**

For flows with high or medium severity issues, conduct thorough review across three dimensions. Document specific issues with file paths, line numbers, and code examples. Propose 2-3 alternative solutions for significant issues.

### Review Dimensions

**Architecture & Design Patterns**
- Component organization and separation of concerns
- State management (React hooks, prop drilling, state lifting)
- API design (RESTful conventions, request/response formats)
- Data flow (database → API → UI and reverse)
- Code reuse versus duplication
- Framework best practices adherence

**Error Handling & Edge Cases**
- Try/catch coverage in async operations
- API error responses (status codes, messages)
- Frontend error boundaries and fallback UI
- Input validation (client and server)
- File upload validation (size, type, corruption)
- Database operation failures
- Network failures
- Security (SQL injection, XSS, file upload vulnerabilities, CORS)

**Readability & Maintainability**
- Function and component size
- Naming clarity
- Comments (why, not what)
- TypeScript type safety (avoid `any`, use proper interfaces)
- Magic values versus constants
- Code style consistency

## Feature Flows

### Flow 1: Upload Flows

**Single Upload:**
`UploadForm.tsx` → `POST /upload` → OCR pipeline → database

**Bulk Upload:**
`BulkUploadForm.tsx` → `POST /upload/bulk` → batch OCR → database

**Components:**
- Frontend: UploadForm, BulkUploadForm
- API: routes.py (upload endpoints)
- OCR: marker_detector, image_processor, coordinate_transformer, text_extractor, jacoti_parser

**Key Concerns:**
- File validation
- Per-file error handling in bulk operations
- OCR failure scenarios

### Flow 2: Visualization Flows

**Dashboard:**
`Dashboard.tsx` → `GET /tests` → data aggregation → chart components

**Individual Viewer:**
`TestViewer.tsx` → `GET /tests/:id` → single test display

**Components:**
- Frontend: Dashboard, TestViewer, AudiogramChart, AudiogramAnimation, FrequencyTrendChart, TestCalendarHeatmap, ComparisonGrid
- API: routes.py (read endpoints)

**Key Concerns:**
- Data transformation
- Chart rendering performance
- Empty state handling

### Flow 3: Data Management Flows

**List View:**
`TestList.tsx` → `GET /tests` → display, filter, sort

**Review/Edit:**
`TestReviewEdit.tsx` → `GET /tests/:id` → `PUT /tests/:id` → database update

**Components:**
- Frontend: TestList, TestReviewEdit
- API: routes.py (CRUD endpoints)
- Database: db_utils.py

**Key Concerns:**
- Data validation on updates
- Concurrent modification handling
- Referential integrity

### Cross-Cutting Concerns

**API Client:**
`lib/api.ts` - HTTP requests, error handling patterns

**Navigation:**
Routing, state preservation

**Database:**
`db_utils.py` - connection handling, query patterns

**Initialization:**
`app.py`, `main.tsx` - application bootstrap

## Output Format

### Phase 1: Quick Scan Matrix

```markdown
# Code Review Quick Scan Results

## Findings Summary
| Flow | High Severity | Medium Severity | Low Severity | Deep Dive? |
|------|---------------|-----------------|--------------|------------|
| Upload (Single) | 3 | 5 | 2 | Yes |
| Upload (Bulk) | 2 | 4 | 1 | Yes |
| Dashboard | 1 | 3 | 4 | Yes |
| ... | ... | ... | ... | ... |

## High-Level Patterns Identified
- Pattern 1: Missing error handling in API calls
- Pattern 2: No input validation on frontend forms
- ...
```

### Phase 3: Deep Dive Document

```markdown
# Code Review Detailed Findings

## Flow: Upload (Single)

### Architecture & Design Patterns

#### Issue: Tight coupling between UI and OCR logic
**Severity:** Medium
**Location:** `UploadForm.tsx:45-67`, `routes.py:23-89`
**Description:** Upload form directly depends on OCR response structure...

**Alternatives:**

1. **Adapter pattern** - Create abstraction layer between API and OCR
   - Pro: Easy to swap OCR providers
   - Con: Additional complexity

2. **Event-driven** - OCR publishes results, API subscribes
   - Pro: Better decoupling
   - Con: Async complexity

3. **Keep current + validation** - Add type guards and validation
   - Pro: Minimal change
   - Con: Still coupled

[Additional issues...]

### Error Handling & Edge Cases
[Issues documented with same structure...]

### Readability & Maintainability
[Issues documented with same structure...]
```

## Workflow Integration

This code review feeds into the following workflow:

1. **Code Review** → Produces detailed findings document
2. **Design Document** (brainstorming skill) → Refines findings into improvement strategy
3. **Implementation Plan** (writing-plans skill) → Creates actionable tasks
4. **Execution** (executing-plans or subagent-driven-development) → Implements improvements
5. **Testing** (test-driven-development) → Adds tests during implementation
6. **Verification** (verification-before-completion) → Ensures quality

## Review Methods

**Quick Scan:**
- Grep for patterns (missing try/catch, unhandled errors)
- Skim key files
- Identify code smells and anti-patterns
- Document in matrix format

**Deep Dive:**
- Read complete files for selected flows
- Trace data flow end-to-end
- Analyze code against three dimensions
- Document with file paths, line numbers, snippets
- Propose alternatives for significant issues

## Timeline

- Phase 1 (Quick Scan): 1-2 hours
- Phase 2 (Categorization): 30 minutes
- Phase 3 (Deep Dive): 2-4 hours
- **Total: 4-7 hours**

## Success Criteria

Review succeeds when:
1. All three flows have been scanned for issues
2. High and medium severity issues are documented with specific locations
3. Significant issues have 2-3 proposed alternatives
4. Findings document is ready for design phase
5. Systemic patterns are identified for strategic improvements
