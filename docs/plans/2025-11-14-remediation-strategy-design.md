# Remediation Strategy Design - Hearing Test Tracker

**Date:** 2025-11-14
**Based On:** Code Review Findings (82 issues across 9 flows)
**Estimated Effort:** 57-72 hours base + 30% TDD overhead = ~90 hours total
**Timeline:** 11 days intensive (1.5-2 weeks)
**Approach:** Test-Driven Phase Implementation with Daily Milestones

---

## Executive Summary

This document outlines the complete remediation strategy for the Hearing Test Tracker application based on the comprehensive code review that identified 82 issues (15 Critical, 46 Medium, 21 Low).

**Strategic Decisions:**
- **Goal:** Complete professional application (all 4 phases)
- **Timeline:** 1-2 weeks intensive full-time focus
- **Execution:** Pair programming with Claude throughout
- **Testing:** Strict Test-Driven Development (TDD) for all fixes

**Key Insight:** The 4 phases build on each other - proper error handling requires auth infrastructure, transaction management requires error handlers, and observability requires all systems in place.

---

## Overall Strategy & Approach

**Strategy: Test-Driven Phase Implementation with Daily Milestones**

We'll implement all 4 phases sequentially using strict TDD, with each phase completing in 2-4 days. Every fix starts with a failing test that proves the vulnerability exists, then implementation makes the test pass.

### Phase Order & Timeline

1. **Phase 1: Critical Security** (Days 1-3, 20-25h)
   - Authentication/Authorization
   - CORS restriction
   - File upload security
   - Global error handlers
   - Environment configuration

2. **Phase 2: Data Integrity** (Days 4-6, 15-20h)
   - Transaction management
   - Two-phase commit for files
   - Backend validation (Pydantic)
   - Frontend validation (react-hook-form + zod)
   - Error boundaries

3. **Phase 3: Error Handling & UX** (Days 7-9, 12-15h)
   - Query error states
   - Mutation error handling
   - QueryClient configuration
   - Dirty state tracking
   - Safe type assertions

4. **Phase 4: Observability & Polish** (Days 10-11, 10-12h)
   - Structured logging
   - Error tracking
   - Enhanced health checks
   - Pagination
   - Safe date handling
   - 404 route

### Daily Workflow Pattern

**Morning (1-2 hours):** Write tests for 2-3 related fixes
- Focus on one subsystem (e.g., all auth endpoints)
- Write tests that prove vulnerabilities exist
- Commit tests with clear descriptions

**Midday (2-4 hours):** Implement fixes until tests pass
- Minimal implementation to make tests green
- No gold-plating or scope creep
- Run tests frequently

**Afternoon (1-2 hours):** Refactor, manual testing, commit
- Clean up code while keeping tests green
- Manual smoke testing of affected features
- Commit working fixes with descriptive messages
- Update todo list for next day

**End of day:** Review progress, plan next day's fixes
- Check off completed todos
- Identify any blockers or risks
- Plan tomorrow's test cases

### Key Principles

1. **Red-Green-Refactor:** Every fix starts with a failing test
2. **Batch related fixes:** Group similar work for momentum
3. **Commit frequently:** After each passing test or small fix
4. **No regressions:** Existing functionality must keep working
5. **YAGNI ruthlessly:** Implement only what's needed to pass tests

### Testing Stack

**Backend:**
- pytest + pytest-flask for API tests
- Fixture-based test data
- Database transaction rollback between tests

**Frontend:**
- Vitest + React Testing Library for component tests
- MSW (Mock Service Worker) for API mocking
- User-centric testing (test behavior, not implementation)

**E2E (Optional, time permitting):**
- Playwright for critical user flows
- Auth flow, upload flow, edit flow

---

## Phase 1: Critical Security (Days 1-3)

**Goal:** Eliminate all critical security vulnerabilities - no auth, CORS exposure, file upload risks, error disclosure.

### Day 1: Foundation (8-10h)

#### 1. Environment Configuration (2h)
**Why First:** All security features need config (SECRET_KEY, allowed origins, file size limits)

**Implementation:**
- Create `backend/config.py` with environment-based config classes
- Add `.env.example` with all required variables
- Add `.env` to `.gitignore`
- Validate production config (fail fast if SECRET_KEY missing, DEBUG=True in production)

**Tests:**
```python
def test_config_loads_from_environment():
    """Test configuration reads from environment variables."""

def test_production_config_requires_secret_key():
    """Test production fails without SECRET_KEY."""

def test_debug_mode_disabled_in_production():
    """Test DEBUG=False enforced in production."""
```

**Acceptance Criteria:**
- ✅ Config loads from .env file
- ✅ Production startup fails without SECRET_KEY
- ✅ All config values documented in .env.example

#### 2. Global Error Handlers (3h)
**Why Before Auth:** Auth failures need proper error responses (not stack traces)

**Implementation:**
- Add Flask @app.errorhandler for 404, 500, 413, Exception
- Consistent JSON error response format: `{"error": "message", "status": code}`
- No stack traces in production (only in logs)
- Request ID in all error responses for debugging

**Tests:**
```python
def test_404_returns_json_not_html():
    """Test 404 errors return JSON, not default HTML."""

def test_500_hides_stack_trace_in_production():
    """Test 500 errors don't leak internal details."""

def test_413_file_too_large_handled():
    """Test oversized uploads return 413 with clear message."""

def test_unhandled_exception_returns_500():
    """Test unexpected errors return generic 500."""
```

**Acceptance Criteria:**
- ✅ All error types return consistent JSON
- ✅ No stack traces visible in responses
- ✅ Error responses include helpful messages

#### 3. CORS Restriction (2h)
**Why Before Auth:** Auth tokens need proper CORS headers

**Implementation:**
- Read allowed origins from environment variable
- Default to localhost:5173, localhost:3000 for development
- Require explicit production origins (fail fast if not set)
- Support credentials for auth cookies/headers

**Tests:**
```python
def test_allowed_origin_accepted():
    """Test requests from allowed origins succeed."""

def test_disallowed_origin_rejected():
    """Test requests from unknown origins rejected."""

def test_cors_credentials_supported():
    """Test credentials allowed for auth."""

def test_production_requires_explicit_origins():
    """Test production fails without CORS_ALLOWED_ORIGINS."""
```

**Acceptance Criteria:**
- ✅ Only configured origins can access API
- ✅ Credentials supported for auth
- ✅ Production requires explicit origin list

**Day 1 Deliverable:** Secure foundation with config, error handling, CORS. All tests passing.

---

### Day 2: Authentication (8-10h)

#### 4. JWT Authentication System (5h)
**Implementation:**
- Create `user` table (id, email, password_hash, created_at)
- POST /api/auth/register endpoint (email/password)
- POST /api/auth/login endpoint (returns JWT token)
- `@require_auth` decorator (validates JWT, sets g.user_id)
- Password hashing with bcrypt
- Token expiration (24 hours)

**Tests:**
```python
def test_user_registration_success():
    """Test user can register with valid email/password."""

def test_user_registration_duplicate_email_rejected():
    """Test duplicate email registration rejected."""

def test_login_with_valid_credentials_returns_token():
    """Test login returns valid JWT token."""

def test_login_with_invalid_credentials_rejected():
    """Test wrong password rejected."""

def test_expired_token_rejected():
    """Test expired tokens return 401."""

def test_invalid_token_rejected():
    """Test malformed tokens return 401."""

def test_missing_token_rejected():
    """Test requests without token return 401."""
```

**Acceptance Criteria:**
- ✅ Users can register and login
- ✅ Passwords securely hashed
- ✅ JWT tokens generated and validated
- ✅ Token expiration enforced

#### 5. Protect All Endpoints (3h)
**Implementation:**
- Add `user_id` column to `hearing_test` table
- Add `@require_auth` to all CRUD endpoints
- Filter all queries by `g.user_id` (users only see their data)
- Check ownership before PUT/DELETE (403 if not owner)
- Update frontend to store/send JWT token

**Tests:**
```python
def test_unauthenticated_request_rejected():
    """Test requests without auth token rejected."""

def test_user_only_sees_own_tests():
    """Test users only retrieve their own test data."""

def test_user_cannot_update_other_user_test():
    """Test updating another user's test returns 403."""

def test_user_cannot_delete_other_user_test():
    """Test deleting another user's test returns 403."""

def test_authenticated_user_can_upload():
    """Test authenticated users can upload files."""
```

**Acceptance Criteria:**
- ✅ All endpoints require authentication
- ✅ Users isolated to their own data
- ✅ Ownership checks prevent unauthorized access
- ✅ Frontend stores and sends JWT tokens

**Day 2 Deliverable:** Full authentication system protecting all data. Users isolated.

---

### Day 3: File Upload Security (6-8h)

#### 6. File Upload Defense-in-Depth (6h)
**Implementation:**
- File size limits via `MAX_CONTENT_LENGTH` config
- MIME type validation using python-magic (check magic numbers)
- Filename sanitization (secure_filename + UUID prefix)
- Rate limiting with Flask-Limiter (10 uploads/minute per user)
- Virus scanning hook (placeholder for future ClamAV integration)

**Tests:**
```python
def test_oversized_file_rejected():
    """Test files exceeding size limit return 413."""

def test_invalid_mime_type_rejected():
    """Test non-image files rejected (e.g., .exe renamed to .jpg)."""

def test_filename_sanitized():
    """Test malicious filenames sanitized (path traversal prevented)."""

def test_upload_rate_limiting():
    """Test excessive uploads rate limited."""

def test_valid_file_upload_succeeds():
    """Test legitimate image uploads work."""

def test_bulk_upload_total_size_limit():
    """Test bulk uploads respect total size limit."""

def test_bulk_upload_file_count_limit():
    """Test bulk uploads limited to max file count."""
```

**Acceptance Criteria:**
- ✅ File size limits enforced
- ✅ MIME type validation prevents malicious files
- ✅ Filenames sanitized (no path traversal)
- ✅ Rate limiting prevents abuse
- ✅ Bulk uploads have additional limits

**Day 3 Deliverable:** Hardened file upload system. All security vectors addressed.

---

## Phase 2: Data Integrity (Days 4-6)

**Goal:** Prevent data corruption through proper transaction management and comprehensive input validation.

### Day 4: Transaction Infrastructure (6-8h)

#### 1. Transaction Context Manager (3h)
**Implementation:**
- Create `get_transaction()` context manager in `db_utils.py`
- Automatic commit on success, rollback on exception
- Nested transaction support (savepoints)
- Connection pooling

**Tests:**
```python
def test_transaction_commits_on_success():
    """Test successful operations commit."""

def test_transaction_rolls_back_on_exception():
    """Test failures roll back all changes."""

def test_nested_transactions_with_savepoints():
    """Test nested transactions use savepoints."""

def test_transaction_isolation():
    """Test concurrent transactions don't interfere."""
```

**Acceptance Criteria:**
- ✅ All database operations use transactions
- ✅ Failures automatically roll back
- ✅ No manual commit() calls outside transaction manager

#### 2. Two-Phase Commit for Files (3h)
**Implementation:**
- Save uploaded files to temporary directory first
- Insert database record within transaction
- Move file from temp to final location on commit
- Delete temp file on rollback
- Cleanup orphaned files on startup

**Tests:**
```python
def test_file_saved_on_db_success():
    """Test file moved to final location when DB succeeds."""

def test_file_deleted_on_db_failure():
    """Test temp file cleaned up when DB fails."""

def test_no_orphaned_files_after_failure():
    """Test failures don't leave files in filesystem."""

def test_orphaned_file_cleanup_on_startup():
    """Test startup cleans files without DB records."""
```

**Acceptance Criteria:**
- ✅ Files saved atomically with database records
- ✅ No orphaned files on failures
- ✅ Cleanup job removes stranded files

**Day 4 Deliverable:** Robust transaction infrastructure. No data corruption possible.

---

### Day 5: Backend Validation (6-8h)

#### 3. Pydantic Request Schemas (4h)
**Implementation:**
- Create Pydantic models for all request bodies
- `CreateTestSchema`, `UpdateTestSchema`, `UploadFileSchema`
- Range validation (threshold_db: 0-120, dates valid)
- UUID format validation
- Custom validators for business rules

**Tests:**
```python
def test_valid_test_data_accepted():
    """Test valid data passes schema validation."""

def test_threshold_out_of_range_rejected():
    """Test threshold_db outside 0-120 rejected."""

def test_invalid_date_rejected():
    """Test malformed dates rejected."""

def test_invalid_uuid_rejected():
    """Test malformed UUIDs rejected."""

def test_missing_required_field_rejected():
    """Test missing required fields rejected."""
```

**Acceptance Criteria:**
- ✅ All POST/PUT endpoints have schemas
- ✅ Invalid data rejected with clear errors
- ✅ Validation errors return 400 with field details

#### 4. Apply Validation to All Endpoints (3h)
**Implementation:**
- Integrate Pydantic schemas into route handlers
- Return 400 with field-level validation errors
- Validate before touching database

**Tests:**
```python
def test_create_test_validates_input():
    """Test POST /tests validates request body."""

def test_update_test_validates_input():
    """Test PUT /tests/:id validates request body."""

def test_upload_validates_metadata():
    """Test upload endpoint validates metadata."""

def test_validation_error_format():
    """Test validation errors return structured format."""
```

**Acceptance Criteria:**
- ✅ Invalid requests never reach database
- ✅ Errors include specific field failures
- ✅ Users see helpful validation messages

**Day 5 Deliverable:** Comprehensive backend validation. Invalid data impossible.

---

### Day 6: Frontend Validation + Error Boundaries (5-7h)

#### 5. React Hook Form + Zod (3h)
**Implementation:**
- Add react-hook-form + zod to all forms
- Client-side validation before API calls
- Match backend validation rules
- Real-time field validation
- Clear error messages

**Tests:**
```tsx
test('upload form validates file type', () => {
  // Test form shows error for invalid file type
})

test('edit form validates threshold range', () => {
  // Test form prevents threshold outside 0-120
})

test('form prevents submission when invalid', () => {
  // Test submit button disabled with errors
})

test('form shows server validation errors', () => {
  // Test backend validation errors displayed
})
```

**Acceptance Criteria:**
- ✅ Forms validate before API calls
- ✅ Real-time validation feedback
- ✅ Server errors displayed in forms

#### 6. React Error Boundaries (3h)
**Implementation:**
- Root-level ErrorBoundary in `main.tsx`
- Feature-level boundaries for Dashboard, TestViewer
- Fallback UI with error message and recovery
- Error reporting integration (send to backend logger)

**Tests:**
```tsx
test('error boundary catches render errors', () => {
  // Test component errors caught
})

test('error boundary shows fallback UI', () => {
  // Test user sees error message, not white screen
})

test('error boundary allows recovery', () => {
  // Test user can return to dashboard
})

test('error boundary reports errors', () => {
  // Test errors sent to logging system
})
```

**Acceptance Criteria:**
- ✅ No uncaught errors crash app
- ✅ Users see helpful error UI
- ✅ Errors reported for debugging

**Day 6 Deliverable:** Bulletproof forms and error handling. Users never see crashes.

---

## Phase 3: Error Handling & UX (Days 7-9)

**Goal:** Transform application from "works on happy path" to "gracefully handles all error scenarios" with professional UX.

### Day 7: Query Error States (4-6h)

#### 1. Add Error Handling to All useQuery Calls (3h)
**Implementation:**
- Handle `isError` and `error` in Dashboard, TestViewer, TestReviewEdit
- Show error UI with retry button
- Clear error messages extracted from API responses
- Loading states with skeletons

**Tests:**
```tsx
test('dashboard shows error when API fails', () => {
  // Mock API failure, verify error UI shown
})

test('test viewer allows retry after error', () => {
  // Test retry button refetches data
})

test('loading state shown while fetching', () => {
  // Test skeleton UI during loading
})
```

**Acceptance Criteria:**
- ✅ All queries handle error state
- ✅ Users can retry failed requests
- ✅ Error messages are clear and actionable

#### 2. Configure QueryClient with Retry Logic (2h)
**Implementation:**
- Global retry configuration (3 attempts, exponential backoff)
- Custom retry logic (don't retry 401/403/400, do retry 500/503)
- Stale time and cache configuration
- Default error handler

**Tests:**
```tsx
test('transient errors auto-retry', () => {
  // Test 500 errors retry up to 3 times
})

test('auth errors do not retry', () => {
  // Test 401 fails immediately
})

test('exponential backoff applied', () => {
  // Test retry delays increase
})
```

**Acceptance Criteria:**
- ✅ Transient failures retry automatically
- ✅ Auth/validation errors don't retry
- ✅ Retry delays increase exponentially

**Day 7 Deliverable:** Robust query error handling. Transient failures invisible to users.

---

### Day 8: Mutation Error Handling (4-5h)

#### 3. Add onError to All Mutations (3h)
**Implementation:**
- Upload, update, delete mutations show error notifications
- Optimistic updates roll back on failure
- Error messages extracted from API responses
- Success notifications on completion

**Tests:**
```tsx
test('failed upload shows error notification', () => {
  // Mock upload failure, verify notification
})

test('optimistic update reverts on error', () => {
  // Test UI rolls back on failed mutation
})

test('successful mutation shows confirmation', () => {
  // Test success notification displayed
})
```

**Acceptance Criteria:**
- ✅ All mutations handle errors
- ✅ Optimistic updates revert on failure
- ✅ Users see clear success/failure feedback

#### 4. Axios Error Interceptor (2h)
**Implementation:**
- Centralized error transformation in `api.ts`
- Extract error messages from API responses
- Auto-logout on 401 (redirect to login)
- Format validation errors nicely (field-level)

**Tests:**
```tsx
test('401 triggers automatic logout', () => {
  // Test unauthorized requests redirect to login
})

test('validation errors formatted for forms', () => {
  // Test 400 errors transformed to field errors
})

test('generic errors have fallback message', () => {
  // Test unknown errors show generic message
})
```

**Acceptance Criteria:**
- ✅ Consistent error handling across app
- ✅ Auth failures trigger logout
- ✅ Error messages user-friendly

**Day 8 Deliverable:** Comprehensive mutation error handling. Users never lose data or see cryptic errors.

---

### Day 9: UX Polish (3-4h)

#### 5. Dirty State Tracking (2h)
**Implementation:**
- Track unsaved changes in TestReviewEdit form
- Block navigation with confirmation dialog
- Clear dirty state after successful save
- Warn on browser close with unsaved changes

**Tests:**
```tsx
test('navigation blocked with unsaved changes', () => {
  // Test user must confirm before leaving
})

test('navigation allowed when no changes', () => {
  // Test clean state allows navigation
})

test('dirty state cleared after save', () => {
  // Test successful save clears dirty flag
})
```

**Acceptance Criteria:**
- ✅ Users can't accidentally lose edits
- ✅ Confirmation only when needed
- ✅ Save clears dirty state

#### 6. Fix Unsafe Type Assertions (2h)
**Implementation:**
- Validate `testDate` exists before `.toISOString()`
- Show validation error if required fields missing
- Disable save button until form valid
- Type guards for nullable values

**Tests:**
```tsx
test('save validates required fields', () => {
  // Test null date shows validation error
})

test('save button disabled when invalid', () => {
  // Test button disabled with missing data
})

test('null date handled gracefully', () => {
  // Test null values don't crash
})
```

**Acceptance Criteria:**
- ✅ No unsafe type assertions remain
- ✅ Validation prevents crashes
- ✅ Users see clear error messages

**Day 9 Deliverable:** Professional UX with dirty state tracking and safe type handling.

---

## Phase 4: Observability & Polish (Days 10-11)

**Goal:** Add production-ready logging, monitoring, and performance optimizations.

### Day 10: Logging & Monitoring (5-6h)

#### 1. Structured Logging Setup (3h)
**Implementation:**
- Python logging with JSON formatter
- Request/response logging middleware
- Log: user_id, endpoint, method, status, duration, request_id
- Error logging with full context (not in response)
- Log levels (DEBUG, INFO, WARNING, ERROR)

**Tests:**
```python
def test_request_logged():
    """Test requests written to log."""

def test_request_id_in_logs():
    """Test each request has unique ID."""

def test_errors_logged_with_context():
    """Test errors include user_id, request_id, stack trace."""

def test_sensitive_data_not_logged():
    """Test passwords/tokens not in logs."""
```

**Acceptance Criteria:**
- ✅ All requests logged with context
- ✅ Errors logged with full details
- ✅ No sensitive data in logs

#### 2. Enhanced Health Check (1h)
**Implementation:**
- Check database connectivity
- Check disk space for uploads
- Return detailed status (healthy/degraded/unhealthy)
- Include version, uptime

**Tests:**
```python
def test_health_check_healthy_state():
    """Test healthy system returns 200."""

def test_health_check_db_down():
    """Test DB failure returns 503."""

def test_health_check_includes_version():
    """Test response includes app version."""
```

**Acceptance Criteria:**
- ✅ Health check validates all dependencies
- ✅ Returns appropriate status codes
- ✅ Useful for load balancer monitoring

#### 3. Error Tracking Integration (Optional, 1h)
**Implementation:**
- Sentry integration for production errors
- Capture user context (user_id, request_id)
- Group errors by type
- Release tracking

**Acceptance Criteria:**
- ✅ Production errors reported to Sentry
- ✅ Errors grouped intelligently
- ✅ User context attached

**Day 10 Deliverable:** Production observability. Can debug issues from logs and error tracking.

---

### Day 11: Performance & Polish (4-5h)

#### 4. Backend Pagination (2h)
**Implementation:**
- Add `page` and `page_size` query params to GET /tests
- Return total count for pagination UI
- Default page_size=20, max=100
- Validate pagination params

**Tests:**
```python
def test_pagination_returns_correct_page():
    """Test page parameter works."""

def test_pagination_returns_total_count():
    """Test response includes total count."""

def test_pagination_validates_params():
    """Test invalid page/page_size rejected."""

def test_pagination_max_page_size_enforced():
    """Test page_size capped at 100."""
```

**Acceptance Criteria:**
- ✅ Large datasets paginated
- ✅ Total count enables UI pagination
- ✅ Parameters validated

#### 5. Safe Date Handling Utility (1h)
**Implementation:**
- Create `parseDate()` utility using date-fns
- Validate dates before parsing
- Handle invalid dates gracefully
- Replace unsafe `new Date()` calls

**Tests:**
```tsx
test('parseDate handles valid dates', () => {
  // Test valid ISO dates parsed
})

test('parseDate rejects invalid dates', () => {
  // Test malformed dates return null
})

test('parseDate used in charts', () => {
  // Test charts don't crash on bad dates
})
```

**Acceptance Criteria:**
- ✅ Date parsing centralized
- ✅ Invalid dates handled gracefully
- ✅ No NaN in date calculations

#### 6. Frontend 404 Route (1h)
**Implementation:**
- Add catch-all route in React Router
- Professional "Page Not Found" UI
- Link back to dashboard
- Log 404s for debugging

**Tests:**
```tsx
test('unknown routes show 404 page', () => {
  // Test /unknown shows 404 UI
})

test('404 page links to dashboard', () => {
  // Test user can navigate back
})
```

**Acceptance Criteria:**
- ✅ Unknown routes show helpful UI
- ✅ Users can navigate back easily

---

### Day 11 End: Final Testing & Documentation (1-2h)

**Tasks:**
1. Run full test suite (backend + frontend)
2. Manual smoke testing:
   - Register, login, logout
   - Upload single file
   - Upload bulk files
   - View dashboard
   - Edit test
   - Delete test
   - Trigger errors (network failure, validation)
3. Update README:
   - Environment setup instructions
   - Required environment variables
   - Testing commands
   - Deployment checklist
4. Final commit and tag release

**Day 11 Deliverable:** Production-ready application with full test coverage and documentation.

---

## Testing Strategy

### TDD Cycle for Each Fix

1. **RED:** Write test that proves vulnerability/bug exists
2. **GREEN:** Implement minimal fix to make test pass
3. **REFACTOR:** Clean up code while keeping tests green
4. **REGRESSION:** Run full test suite to ensure nothing broke

### Test Coverage Targets

- **Phase 1 (Security):** 100% - Every auth path, CORS scenario, file upload validation
- **Phase 2 (Data Integrity):** 100% - All transaction paths, validation rules
- **Phase 3 (Error Handling):** 80% - All error states, representative edge cases
- **Phase 4 (Observability):** 60% - Critical logging paths, happy path verification

### Test Organization

```
backend/tests/
  conftest.py                  # Fixtures, test database setup
  test_auth.py                 # JWT, login, permissions
  test_security.py             # CORS, error handlers, file upload
  test_transactions.py         # Rollback, two-phase commit
  test_validation.py           # Pydantic schemas
  test_api_routes.py           # Integration tests for endpoints

frontend/src/__tests__/
  components/
    ErrorBoundary.test.tsx     # Error boundary behavior
    UploadForm.test.tsx        # Form validation
  pages/
    Dashboard.test.tsx         # Error states, loading
    TestViewer.test.tsx        # Query errors, retry
  lib/
    api.test.ts                # Error interceptor, retry logic
```

### Testing Philosophy

**Backend Tests:**
- Use pytest fixtures for test data (don't duplicate setup)
- Roll back database after each test (fast, isolated)
- Test one behavior per test (clear failure messages)
- Integration tests for critical flows (auth + upload + query)

**Frontend Tests:**
- Test user behavior, not implementation (what user sees/does)
- Mock API calls with MSW (consistent, fast)
- Avoid testing library internals (React Query, form state)
- Focus on error states (happy path is obvious)

**What NOT to test:**
- Third-party library behavior (trust Flask, React Query, etc.)
- Configuration parsing (trust dotenv, Pydantic)
- Trivial getters/setters
- Auto-generated code

---

## Risk Mitigation

### Risk 1: Tests Take Longer Than Estimated

**Probability:** Medium
**Impact:** High (could extend timeline to 2+ weeks)

**Mitigation:**
- Focus on critical path tests first (auth, transactions, file upload)
- Defer edge case tests to end of phase
- If Day 2 ends without auth complete, skip rate limiting tests (nice-to-have)
- Track test writing time separately from implementation time

**Trigger:** If any day ends >2 hours behind schedule

**Response:** Cut scope for that phase (move lower-priority items to Phase 4 or future)

### Risk 2: Breaking Changes to Existing Functionality

**Probability:** Medium
**Impact:** Medium (requires rework, delays progress)

**Mitigation:**
- Write tests for existing behavior BEFORE making changes
- Run full test suite after each commit
- Manual smoke testing at end of each day
- Keep commits small and focused

**Trigger:** If manual testing reveals regression

**Response:**
1. Stop current work immediately
2. Write test that proves regression
3. Fix regression before continuing
4. Review why test didn't catch it

### Risk 3: Scope Creep (Finding New Issues During Implementation)

**Probability:** High
**Impact:** Medium (distracts from plan, extends timeline)

**Mitigation:**
- Document new issues in `docs/future-improvements.md`
- Don't fix issues not in code review findings
- Resist temptation to "improve while we're here"
- Stick to TDD (if no test, no implementation)

**Trigger:** Any issue not in the 82 identified issues

**Response:**
1. Document issue with severity
2. Add to backlog
3. Continue with current plan
4. Review backlog after Phase 4 completion

### Risk 4: Authentication Implementation Complexity

**Probability:** Medium
**Impact:** High (Day 2 could extend to Day 3, cascade delays)

**Mitigation:**
- Use established libraries (PyJWT, bcrypt, not custom crypto)
- Start with simplest auth (JWT only, no refresh tokens initially)
- Test incrementally (register, then login, then protect endpoints)
- Reference existing Flask JWT tutorials

**Trigger:** If Day 2 extends past 10 hours

**Response:**
- Simplify: Remove refresh tokens (use longer expiration)
- Simplify: Skip email verification initially
- Simplify: Basic RBAC (just logged in vs. not logged in)

### Risk 5: Test Environment Setup Issues

**Probability:** Low
**Impact:** High (blocks all testing)

**Mitigation:**
- Set up test environment on Day 0 (before Phase 1 starts)
- Use separate test database (not development DB)
- Containerize test environment (Docker for consistency)
- Document setup in README

**Trigger:** Tests fail to run at all

**Response:**
- Pair debug with Claude to resolve quickly
- Don't continue implementation without working tests
- Consider simplified test setup (sqlite for tests instead of postgres)

---

## Success Criteria

### Phase Completion Definition

A phase is complete when:
- ✅ All planned tests for phase passing
- ✅ Manual testing of phase features successful
- ✅ No regressions in existing functionality (all tests green)
- ✅ Code committed with descriptive messages
- ✅ Phase documented in commit history
- ✅ TodoWrite todos marked complete

### Project Completion Definition

The project is complete when:
- ✅ All 82 issues addressed or documented as deferred
- ✅ Test coverage meets targets (≥80% overall)
- ✅ Application deployable to production (config validated, secrets setup, health checks working)
- ✅ README updated with setup instructions, environment variables, testing commands
- ✅ No critical or high-severity security vulnerabilities remain
- ✅ Manual end-to-end testing passes (register → login → upload → view → edit → delete → logout)
- ✅ All tests passing (backend + frontend)

### Post-Completion Activities

After all 4 phases complete:

1. **Staging Deployment**
   - Deploy to staging environment
   - Validate environment configuration
   - Test with production-like data

2. **Security Audit**
   - Manual penetration testing (test auth bypass, file upload exploits)
   - Automated security scan (Bandit for Python, npm audit for frontend)
   - Review all TODO comments for security implications

3. **Performance Baseline**
   - Measure response times for all endpoints
   - Load testing (100 concurrent users)
   - Database query performance (check for N+1 queries)

4. **User Acceptance Testing**
   - Test with real audiogram images
   - Verify OCR metadata extraction still works
   - Validate chart rendering with real data
   - Get feedback on error messages and UX

5. **Production Deployment**
   - Set up production environment variables
   - Configure production database
   - Set up error tracking (Sentry)
   - Deploy application
   - Monitor logs and errors for first 24 hours

---

## Appendix: Alternative Approaches Considered

### Authentication: JWT vs. Session-Based

**Chosen:** JWT (Stateless tokens)

**Alternative:** Session-based auth (server-side sessions in Redis)

**Rationale:**
- JWT simpler for single-server deployment (no Redis dependency)
- Stateless scales better (can add servers without session sharing)
- Matches modern SPA architecture (frontend already using API client)

**Trade-off:** Can't revoke JWTs before expiration (acceptable for 24h expiration)

### Testing: TDD vs. Test-After

**Chosen:** TDD (tests first)

**Alternative:** Implement first, then write tests

**Rationale:**
- Security fixes MUST have tests (can't validate without proof)
- TDD prevents over-engineering (only code needed for tests)
- Learning value is highest (understand problem before solution)

**Trade-off:** 30% slower implementation (90h vs. 72h baseline)

### Execution: Sequential vs. Parallel Subagents

**Chosen:** Sequential pairing with Claude

**Alternative:** Parallel subagent execution (multiple independent fixes simultaneously)

**Rationale:**
- Pairing provides learning (understand each fix deeply)
- Reduces merge conflicts (only one area changing at a time)
- Enables TDD discipline (hard to maintain with parallel work)

**Trade-off:** Longer wall-clock time (11 days vs. potentially 6-7 days with parallelization)

### Error Handling: Global Handlers vs. Per-Endpoint

**Chosen:** Global error handlers + per-endpoint specific handling

**Alternative:** Only per-endpoint error handling

**Rationale:**
- Global handlers catch unexpected errors (defensive)
- Consistent error format across all endpoints
- Per-endpoint allows customization where needed

**Trade-off:** Slightly more complex error handling architecture

---

## Next Steps

1. **Write detailed implementation plan** using `/superpowers:write-plan`
   - Break each phase/day into specific tasks
   - Specify verification steps for each task
   - Create bite-sized todos for TodoWrite tracking

2. **Set up test environment** (Day 0)
   - Install pytest, pytest-flask
   - Install Vitest, React Testing Library
   - Create test database
   - Verify tests run

3. **Begin Phase 1, Day 1** with TDD discipline
   - Write first test (config loads from environment)
   - Watch it fail
   - Implement config
   - Watch it pass
   - Commit

4. **Daily standups** (end of each day)
   - Review completed todos
   - Check for risks/blockers
   - Plan next day's work

---

**Document Status:** Ready for implementation planning
**Next Action:** Use `/superpowers:write-plan` to create detailed implementation plan
**Estimated Time to Production:** 11 days intensive work
