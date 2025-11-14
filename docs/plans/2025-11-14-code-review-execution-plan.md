# Code Review Execution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Execute comprehensive code review of untested backend API and frontend code, producing detailed findings document with severity ratings and alternative solutions.

**Architecture:** Three-phase approach: (1) Quick scan all flows for patterns and obvious issues, (2) Categorize findings by severity, (3) Deep dive on high/medium severity flows. Reviews cover architecture, error handling, and maintainability. Outputs feed into design and implementation workflows.

**Tech Stack:** Python/Flask backend, React/TypeScript frontend, code analysis using Read/Grep/Glob tools

---

## Phase 1: Quick Scan (Parallel Execution)

**Parallelization Strategy:** Review all three flows concurrently. Each flow produces independent preliminary findings.

### Task 1A: Quick Scan - Upload Flows (Parallel Track A)

**Files:**
- Read: `frontend/src/components/UploadForm.tsx`
- Read: `frontend/src/components/BulkUploadForm.tsx`
- Read: `backend/api/routes.py` (upload endpoints)
- Read: `backend/api/test_upload.py`
- Create: `docs/review/phase1-upload-flows.md`

**Step 1: Create review output directory**

```bash
mkdir -p docs/review
```

**Step 2: Read and analyze UploadForm.tsx**

Focus areas:
- Error handling around file selection and API calls
- Input validation (file size, type)
- State management patterns
- TypeScript type safety

Look for:
```tsx
// Missing try/catch patterns
const handleUpload = async () => {
  const response = await api.upload(file) // No error handling?
}

// Missing validation
<input type="file" onChange={handleFileChange} /> // Any validation?

// Use of 'any' type
const [data, setData] = useState<any>() // Should be typed
```

**Step 3: Read and analyze BulkUploadForm.tsx**

Focus areas:
- Per-file error handling in bulk operations
- Progress tracking and user feedback
- Abort/cancel functionality
- Memory handling for multiple files

**Step 4: Read and analyze backend upload routes**

Focus areas:
- Input validation on server side
- File upload security (size limits, type validation, sanitization)
- Error responses (status codes, messages)
- Database transaction handling

Look for:
```python
# Missing validation
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']  # No validation?

# Missing error handling
result = process_ocr(file)  # What if OCR fails?

# SQL injection risk
db.execute(f"INSERT INTO tests VALUES ({data})")  # Unsafe?
```

**Step 5: Search for common patterns**

Use Grep to find patterns across upload flow:

```bash
# Missing try/catch in frontend
grep -r "await.*api\." frontend/src/components/UploadForm.tsx frontend/src/components/BulkUploadForm.tsx

# Missing error handling in backend
grep -r "@app.route\|@bp.route" backend/api/

# Input validation
grep -r "request.files\|request.form\|request.json" backend/api/
```

**Step 6: Document findings in phase1-upload-flows.md**

```markdown
# Phase 1 Quick Scan: Upload Flows

## Upload Flow (Single)

### High Severity Issues
- [ ] Issue description | File:line | Pattern category

### Medium Severity Issues
- [ ] Issue description | File:line | Pattern category

### Low Severity Issues
- [ ] Issue description | File:line | Pattern category

## Upload Flow (Bulk)

[Same structure...]

## Patterns Identified
- Pattern name: Description
```

**Step 7: Commit Phase 1A findings**

```bash
git add docs/review/phase1-upload-flows.md
git commit -m "review: Phase 1 quick scan - upload flows"
```

---

### Task 1B: Quick Scan - Visualization Flows (Parallel Track B)

**Files:**
- Read: `frontend/src/pages/Dashboard.tsx`
- Read: `frontend/src/pages/TestViewer.tsx`
- Read: `frontend/src/components/AudiogramChart.tsx`
- Read: `frontend/src/components/AudiogramAnimation.tsx`
- Read: `frontend/src/components/FrequencyTrendChart.tsx`
- Read: `frontend/src/components/TestCalendarHeatmap.tsx`
- Read: `frontend/src/components/ComparisonGrid.tsx`
- Read: `backend/api/routes.py` (GET endpoints)
- Create: `docs/review/phase1-visualization-flows.md`

**Step 1: Read and analyze Dashboard.tsx**

Focus areas:
- Data fetching and loading states
- Error boundaries and fallback UI
- Empty state handling (no tests yet)
- Performance (multiple charts rendering)

Look for:
```tsx
// Missing loading/error states
const { data } = useQuery('/tests') // What about loading/error?

// Missing empty state
{data.map(test => <Chart data={test} />)} // What if data is empty?

// Performance issues
{tests.map(test => <ExpensiveChart test={test} />)} // Memoization?
```

**Step 2: Read and analyze chart components**

For each chart component, check:
- Props validation (PropTypes or TypeScript interfaces)
- Data transformation and edge cases
- Error handling for invalid data
- Accessibility (ARIA labels, keyboard navigation)

**Step 3: Read and analyze TestViewer.tsx**

Focus areas:
- 404 handling (test not found)
- Loading states
- Data refresh patterns
- Route parameter validation

**Step 4: Read and analyze backend GET routes**

Focus areas:
- Query parameter validation
- Error responses (404, 500)
- Data serialization
- Database query efficiency

Look for:
```python
# Missing validation
@app.route('/tests/<test_id>')
def get_test(test_id):
    test = db.query(test_id)  # What if not found? SQL injection?

# Missing error handling
return jsonify(test.to_dict())  # What if to_dict fails?
```

**Step 5: Search for common patterns**

```bash
# Missing error boundaries
grep -r "ErrorBoundary\|componentDidCatch" frontend/src/

# Missing prop validation
grep -r "interface.*Props\|type.*Props" frontend/src/components/

# Loading states
grep -r "isLoading\|loading" frontend/src/pages/
```

**Step 6: Document findings in phase1-visualization-flows.md**

Use same structure as Task 1A.

**Step 7: Commit Phase 1B findings**

```bash
git add docs/review/phase1-visualization-flows.md
git commit -m "review: Phase 1 quick scan - visualization flows"
```

---

### Task 1C: Quick Scan - Data Management Flows (Parallel Track C)

**Files:**
- Read: `frontend/src/pages/TestList.tsx`
- Read: `frontend/src/pages/TestReviewEdit.tsx`
- Read: `frontend/src/lib/api.ts`
- Read: `backend/api/routes.py` (PUT, DELETE endpoints)
- Read: `backend/database/db_utils.py`
- Create: `docs/review/phase1-data-management-flows.md`

**Step 1: Read and analyze TestList.tsx**

Focus areas:
- Pagination/infinite scroll implementation
- Filter and sort functionality
- Delete confirmation UX
- Optimistic updates

Look for:
```tsx
// Missing confirmation
const handleDelete = (id) => {
  deleteTest(id) // No confirmation?
}

// State management issues
const [filter, setFilter] = useState()
const [sort, setSort] = useState() // Lifting state? URL params?
```

**Step 2: Read and analyze TestReviewEdit.tsx**

Focus areas:
- Form validation (client-side)
- Dirty state tracking (unsaved changes)
- Concurrent edit detection
- Optimistic vs pessimistic updates

Look for:
```tsx
// Missing validation
const handleSave = async () => {
  await api.updateTest(id, formData) // Validated?
}

// Missing dirty check
const handleNavigate = () => {
  navigate('/') // What about unsaved changes?
}
```

**Step 3: Read and analyze api.ts**

Focus areas:
- Error handling patterns
- Request/response interceptors
- Authentication/authorization
- Retry logic
- Type safety

Look for:
```typescript
// Inconsistent error handling
async function upload(file: File) {
  return fetch('/upload', { ... }) // Throws? Returns error?
}

// Missing types
async function getData(): Promise<any> { // Should be typed

// No retry logic
fetch(url) // Network failure handling?
```

**Step 4: Read and analyze backend CRUD routes**

Focus areas:
- PUT/PATCH validation
- DELETE cascading/referential integrity
- Concurrent modification handling (optimistic locking)
- Authorization checks

Look for:
```python
# Missing validation
@app.route('/tests/<id>', methods=['PUT'])
def update_test(id):
    data = request.json  # Validated?
    db.update(id, data)  # What fields are allowed?

# Missing authorization
def delete_test(id):
    db.delete(id)  # Can anyone delete?
```

**Step 5: Read and analyze db_utils.py**

Focus areas:
- Connection pooling
- Transaction handling
- Error handling (connection failures, constraint violations)
- SQL injection prevention

**Step 6: Search for common patterns**

```bash
# API error handling
grep -r "catch\|\.then" frontend/src/lib/api.ts

# Form validation
grep -r "validate\|validation\|schema" frontend/src/pages/

# Database transactions
grep -r "begin\|commit\|rollback" backend/database/
```

**Step 7: Document findings in phase1-data-management-flows.md**

Use same structure as Task 1A.

**Step 8: Commit Phase 1C findings**

```bash
git add docs/review/phase1-data-management-flows.md
git commit -m "review: Phase 1 quick scan - data management flows"
```

---

### Task 1D: Quick Scan - Cross-Cutting Concerns

**Files:**
- Read: `frontend/src/App.tsx`
- Read: `frontend/src/main.tsx`
- Read: `frontend/src/components/Navigation.tsx`
- Read: `frontend/src/components/AppLayout.tsx`
- Read: `backend/app.py`
- Read: `backend/config.py`
- Create: `docs/review/phase1-cross-cutting.md`

**Step 1: Read and analyze frontend initialization**

Focus areas:
- Error boundary at root level
- Router configuration
- Global state setup
- Environment variable handling

**Step 2: Read and analyze Navigation and AppLayout**

Focus areas:
- Accessibility
- Mobile responsiveness
- Active route highlighting
- Consistent layout patterns

**Step 3: Read and analyze backend initialization**

Focus areas:
- CORS configuration
- Error handlers (404, 500)
- Logging setup
- Configuration management (secrets, environment)

Look for:
```python
# Insecure configuration
app.config['SECRET_KEY'] = 'hardcoded'  # Should be env var

# Missing CORS
# No CORS headers?

# Missing error handlers
# No @app.errorhandler(500)?
```

**Step 4: Document findings**

```bash
git add docs/review/phase1-cross-cutting.md
git commit -m "review: Phase 1 quick scan - cross-cutting concerns"
```

---

## Phase 2: Severity Categorization (Sequential)

**Note:** This phase MUST run after Phase 1 completes. Cannot be parallelized.

### Task 2: Consolidate and Categorize Findings

**Files:**
- Read: `docs/review/phase1-upload-flows.md`
- Read: `docs/review/phase1-visualization-flows.md`
- Read: `docs/review/phase1-data-management-flows.md`
- Read: `docs/review/phase1-cross-cutting.md`
- Create: `docs/review/phase2-severity-matrix.md`

**Step 1: Create severity matrix template**

```markdown
# Phase 2: Severity Categorization Matrix

## Findings Summary

| Flow | High Severity | Medium Severity | Low Severity | Deep Dive? |
|------|---------------|-----------------|--------------|------------|
| Upload (Single) | 0 | 0 | 0 | TBD |
| Upload (Bulk) | 0 | 0 | 0 | TBD |
| Dashboard | 0 | 0 | 0 | TBD |
| TestViewer | 0 | 0 | 0 | TBD |
| TestList | 0 | 0 | 0 | TBD |
| TestReviewEdit | 0 | 0 | 0 | TBD |
| Cross-Cutting | 0 | 0 | 0 | TBD |

## Severity Definitions

**High:**
- Security vulnerabilities (XSS, SQL injection, file upload attacks)
- Data integrity risks (data loss, corruption)
- Critical error handling gaps (unhandled crashes, silent failures)

**Medium:**
- Poor architecture (tight coupling, violation of separation of concerns)
- Inconsistent patterns (different error handling across similar code)
- Missing validation (input sanitization, type checking)
- UX issues (poor error messages, missing loading states)

**Low:**
- Code style inconsistencies
- Minor redundancy
- Documentation gaps
- Magic numbers/strings

## Deep Dive Decision Criteria

- High severity count ≥ 2: **Required**
- Medium severity count ≥ 4: **Required**
- High + Medium ≥ 5: **Required**
- Otherwise: **Skip** (document patterns only)
```

**Step 2: Review upload flows findings and categorize**

Read `phase1-upload-flows.md` and for each issue:
1. Assign severity (High/Medium/Low)
2. Update count in matrix
3. Move to appropriate severity section

**Step 3: Review visualization flows findings and categorize**

Same process for `phase1-visualization-flows.md`.

**Step 4: Review data management flows findings and categorize**

Same process for `phase1-data-management-flows.md`.

**Step 5: Review cross-cutting findings and categorize**

Same process for `phase1-cross-cutting.md`.

**Step 6: Mark flows for deep dive**

Apply decision criteria to each flow in the matrix.

**Step 7: Identify systemic patterns**

```markdown
## Systemic Patterns Identified

### Pattern: Missing Error Handling in API Calls
**Severity:** High
**Occurrences:** 12 locations across Upload, Dashboard, TestList
**Description:** Async API calls lack try/catch blocks...
**Impact:** Silent failures, poor UX, potential data loss

### Pattern: No Input Validation on Forms
**Severity:** Medium
**Occurrences:** 5 forms across Upload, TestReviewEdit
**Description:** Frontend forms submit without validation...
**Impact:** Poor UX, unnecessary API calls, potential security risk

[Additional patterns...]
```

**Step 8: Commit severity matrix**

```bash
git add docs/review/phase2-severity-matrix.md
git commit -m "review: Phase 2 severity categorization and deep dive selection"
```

---

## Phase 3: Deep Dive Analysis (Parallel Execution)

**Parallelization Strategy:** Deep dive on each flow marked for detailed review concurrently.

**Note:** Only execute deep dive tasks for flows marked "Yes" in Phase 2 matrix.

### Task 3A: Deep Dive - Upload Flows (If Required)

**Files:**
- Read: All files from Task 1A (detailed review)
- Create: `docs/review/phase3-upload-flows-detailed.md`

**Step 1: Create deep dive template**

```markdown
# Deep Dive: Upload Flows

## Flow: Single Upload

### Architecture & Design Patterns

#### Issue 1: [Title]
**Severity:** High/Medium
**Location:** `file/path.tsx:45-67`, `other/file.py:23-89`
**Category:** Architecture

**Description:**
[Detailed description of the issue, why it matters, what problems it causes]

**Current Code:**
```tsx
// Problematic code snippet
```

**Alternatives:**

**Option 1: [Solution Name]** ⭐ Recommended
```tsx
// Proposed code
```
- **Pro:** Benefit 1
- **Pro:** Benefit 2
- **Con:** Drawback 1
- **Con:** Drawback 2

**Option 2: [Alternative Solution]**
```tsx
// Alternative code
```
- **Pro:** Benefit 1
- **Con:** Drawback 1

**Option 3: [Another Alternative]**
```tsx
// Another alternative
```
- **Pro:** Benefit 1
- **Con:** Drawback 1

---

[Additional architecture issues...]

### Error Handling & Edge Cases

[Same structure for error handling issues...]

### Readability & Maintainability

[Same structure for maintainability issues...]

## Flow: Bulk Upload

[Same structure for bulk upload...]
```

**Step 2: Deep dive on UploadForm.tsx architecture**

Read the entire file carefully. For each architectural concern:
1. Document the issue with exact line numbers
2. Explain the problem and impact
3. Propose 2-3 alternatives with code examples
4. Mark recommendation

Focus on:
- Component organization (too large? good separation?)
- State management (useState vs useReducer? Context needed?)
- Side effects (useEffect dependencies, cleanup)
- Code reuse (repeated logic that could be extracted?)

**Step 3: Deep dive on UploadForm.tsx error handling**

For each error scenario:
1. Document missing or inadequate handling
2. Propose solutions with code
3. Consider edge cases

Scenarios to check:
- File selection errors
- API call failures (network, server error, timeout)
- OCR failures
- Validation failures
- Large file handling

**Step 4: Deep dive on UploadForm.tsx maintainability**

Check:
- Function length and complexity
- Variable and function naming
- TypeScript type safety
- Comments (are they needed? are they helpful?)
- Magic values that should be constants

**Step 5: Repeat deep dive for BulkUploadForm.tsx**

Same three-dimension analysis.

**Step 6: Deep dive on backend upload routes**

Same three dimensions for backend code:
- Architecture (route organization, separation of concerns)
- Error handling (all failure paths covered?)
- Maintainability (function length, naming, documentation)

**Step 7: Commit deep dive findings**

```bash
git add docs/review/phase3-upload-flows-detailed.md
git commit -m "review: Phase 3 deep dive - upload flows"
```

---

### Task 3B: Deep Dive - Visualization Flows (If Required)

**Files:**
- Read: All files from Task 1B (detailed review)
- Create: `docs/review/phase3-visualization-flows-detailed.md`

**Step 1: Create deep dive document with same template as 3A**

**Step 2-7: Repeat deep dive process for each visualization component**

Focus areas specific to visualization:
- Chart data transformation (null/undefined handling)
- Performance (memoization, virtualization for large datasets)
- Accessibility (ARIA labels, keyboard navigation, screen readers)
- Responsive design (mobile, tablet, desktop)
- Empty states (no data, loading, error)

**Step 8: Commit deep dive findings**

```bash
git add docs/review/phase3-visualization-flows-detailed.md
git commit -m "review: Phase 3 deep dive - visualization flows"
```

---

### Task 3C: Deep Dive - Data Management Flows (If Required)

**Files:**
- Read: All files from Task 1C (detailed review)
- Create: `docs/review/phase3-data-management-flows-detailed.md`

**Step 1: Create deep dive document with same template as 3A**

**Step 2-7: Repeat deep dive process for CRUD operations**

Focus areas specific to data management:
- Form validation (client and server)
- Optimistic vs pessimistic updates
- Concurrent modification handling
- Delete confirmation and cascading
- API client patterns (consistency, error handling)

**Step 8: Commit deep dive findings**

```bash
git add docs/review/phase3-data-management-flows-detailed.md
git commit -m "review: Phase 3 deep dive - data management flows"
```

---

### Task 3D: Deep Dive - Cross-Cutting Concerns (If Required)

**Files:**
- Read: All files from Task 1D (detailed review)
- Create: `docs/review/phase3-cross-cutting-detailed.md`

**Step 1: Create deep dive document**

**Step 2-5: Review initialization, configuration, security**

Focus areas:
- Configuration management (secrets, environment variables)
- Security (CORS, authentication, authorization)
- Error handling (global error boundaries, API error handlers)
- Logging and monitoring

**Step 6: Commit deep dive findings**

```bash
git add docs/review/phase3-cross-cutting-detailed.md
git commit -m "review: Phase 3 deep dive - cross-cutting concerns"
```

---

## Phase 4: Consolidation and Final Report

### Task 4: Create Final Findings Document

**Files:**
- Read: All phase 2 and phase 3 documents
- Create: `docs/review/code-review-findings.md`

**Step 1: Create consolidated report template**

```markdown
# Code Review Findings - Hearing Test Tracker

**Date:** 2025-11-14
**Scope:** Untested backend API and frontend code
**Reviewer:** Code Review Process
**Status:** Complete

---

## Executive Summary

**Overall Assessment:** [2-3 sentences]

**Key Findings:**
- X High severity issues identified
- Y Medium severity issues identified
- Z Low severity issues identified

**Systemic Patterns:**
1. Pattern name - Brief description
2. Pattern name - Brief description
...

**Recommended Priorities:**
1. Priority area 1
2. Priority area 2
...

---

## Findings by Flow

### Upload Flows

[Summary of upload findings from deep dive]

**High Priority Issues:**
- Issue 1 with location and recommendation
- Issue 2 with location and recommendation

**Medium Priority Issues:**
- Issue 3 with location and recommendation

**Systemic Improvements:**
- Pattern-based recommendation

### Visualization Flows

[Same structure...]

### Data Management Flows

[Same structure...]

### Cross-Cutting Concerns

[Same structure...]

---

## Detailed Findings

[For each high/medium severity issue, include full details from deep dive documents]

---

## Recommendations for Next Steps

**Immediate Actions (High Severity):**
1. Action item with specific files
2. Action item with specific files

**Short-term Improvements (Medium Severity):**
1. Improvement with scope
2. Improvement with scope

**Long-term Refactoring (Patterns):**
1. Systemic improvement
2. Systemic improvement

**Testing Strategy:**
Areas that need test coverage most urgently...

---

## Appendix: Review Process

**Phase 1:** Quick scan of all flows
**Phase 2:** Severity categorization
**Phase 3:** Deep dive on high/medium severity flows
**Total Time:** [Actual time spent]
```

**Step 2: Consolidate executive summary**

Review all phase 2 and phase 3 documents to create accurate counts and identify top patterns.

**Step 3: Consolidate findings by flow**

For each flow, pull key findings from deep dive documents. Prioritize high and medium severity.

**Step 4: Create detailed findings section**

Copy full issue descriptions from phase 3 documents, organized by severity.

**Step 5: Write recommendations**

Based on findings, create actionable next steps organized by priority.

**Step 6: Commit final report**

```bash
git add docs/review/code-review-findings.md
git commit -m "review: consolidated code review findings report"
```

---

## Verification

### Task 5: Verify Completeness

**Step 1: Check all flows reviewed**

Verify documentation exists for:
- [ ] Upload flows (single and bulk)
- [ ] Visualization flows (dashboard, viewer, charts)
- [ ] Data management flows (list, edit, CRUD)
- [ ] Cross-cutting concerns

**Step 2: Verify severity categorization**

- [ ] All issues have severity assigned
- [ ] Deep dive performed on flows meeting criteria
- [ ] Systemic patterns identified

**Step 3: Verify alternative solutions**

For each high/medium severity issue:
- [ ] 2-3 alternatives proposed
- [ ] Code examples provided
- [ ] Pros/cons documented
- [ ] Recommendation marked

**Step 4: Verify output structure**

- [ ] Phase 1 documents exist (4 files)
- [ ] Phase 2 matrix exists
- [ ] Phase 3 deep dive documents exist (for selected flows)
- [ ] Final consolidated report exists

**Step 5: Verify commit history**

```bash
git log --oneline | grep review
```

Expected: Multiple commits showing progression through phases.

**Step 6: Push all findings to remote**

```bash
git push -u origin claude/what-skill-016Q2SC92wLAUfdSBsrrDrTM
```

---

## Success Criteria

✅ All three feature flows scanned for issues
✅ High and medium severity issues documented with specific locations
✅ Significant issues have 2-3 proposed alternatives with code examples
✅ Systemic patterns identified across flows
✅ Final findings document ready for design phase input
✅ All documents committed and pushed

---

## Next Steps After Review

This code review feeds into:

1. **Design Phase** - Use `brainstorming` skill to refine findings into improvement strategy
2. **Implementation Planning** - Use `writing-plans` skill to create detailed fix tasks
3. **Execution** - Use `executing-plans` or `subagent-driven-development` to implement
4. **Testing** - Use `test-driven-development` to add tests during fixes
5. **Verification** - Use `verification-before-completion` before marking complete
