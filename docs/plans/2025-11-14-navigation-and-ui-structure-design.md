# Navigation and UI Structure Design

**Date:** 2025-11-14
**Project:** Hearing Test Tracker
**Status:** Design Complete - Ready for Implementation

---

## Overview

This design adds complete navigation structure and core views to the hearing test tracker application. Currently, the app consists only of an upload form with no way to view uploaded tests or navigate between features. This design implements the foundation for the full application: app shell with navigation, dashboard, test list, test viewer, and review/edit capabilities.

## Design Decisions Summary

### Navigation Pattern
**App Shell with Top Navbar** - Fixed header with navigation links, main content area below. Clean, familiar pattern that works well with future tab-based visualization modes.

### Post-Upload Workflow
**Navigate to Test Viewer** - After upload, user goes directly to detailed view of the uploaded test. For low-confidence results (< 80%), redirect to review/edit page first.

### Review/Edit Page
**Image + Data Side-by-Side** - Original JPEG on left, editable form on right. Appears automatically for low-confidence uploads, or manually via "Edit" button from test viewer.

---

## Application Structure

### Component Hierarchy
```
App.tsx (root)
├── BrowserRouter
│   └── AppShell (Mantine component)
│       ├── AppShell.Header
│       │   └── Navigation (logo + nav links)
│       └── AppShell.Main
│           └── Routes
│               ├── /dashboard → Dashboard
│               ├── /upload → UploadForm
│               ├── /tests → TestList
│               ├── /tests/:id → TestViewer
│               └── /tests/:id/review → TestReviewEdit
```

### Technology Stack Additions
- React Router v6 for routing
- Recharts for audiogram visualization
- Existing: Mantine UI, TanStack React Query, Axios

---

## Navigation Component

### Top Navbar Contents
- **Left:** Logo/Title "Hearing Test Tracker"
- **Center:** Navigation links
  - Dashboard
  - Upload Test
  - All Tests
- **Active State:** Highlight current page link
- **Position:** Fixed at top, always visible

### Routing Configuration
```tsx
<BrowserRouter>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/upload" element={<UploadForm />} />
    <Route path="/tests" element={<TestList />} />
    <Route path="/tests/:id" element={<TestViewer />} />
    <Route path="/tests/:id/review" element={<TestReviewEdit />} />
  </Routes>
</BrowserRouter>
```

---

## Dashboard View

**Route:** `/` or `/dashboard`

**Purpose:** Landing page with overview of all tests and quick access to key actions.

### Layout Sections (Top to Bottom)

#### 1. Stats Cards Row
Three cards showing:
- Total Tests: Count of all uploaded tests
- Latest Test Date: Most recent test date
- Tests This Year: Count for current year

Uses Mantine Grid with responsive columns.

#### 2. Latest Test Card
Prominent card displaying:
- Mini audiogram preview (simplified chart, both ears)
- Test date and location
- Confidence badge (color-coded: green >80%, yellow 60-80%, red <60%)
- "View Details" button → navigates to `/tests/:id`

#### 3. Recent Tests Table
Shows last 10 tests, sorted by date descending.

**Columns:**
- Date
- Location
- Source (Home/Clinic)
- Confidence
- Actions (View button)

**Footer:** "View All Tests" link → navigates to `/tests`

### Empty State
When no tests exist:
- Large icon/illustration
- "No tests yet" heading
- "Upload your first audiogram to get started" text
- Prominent "Upload Test" button

### Data Fetching
- React Query: `useQuery(['dashboard-stats'])`
- Endpoint: `GET /api/tests`
- Calculate stats in frontend (or add new `/api/dashboard/stats` endpoint)

---

## Test Review/Edit Page

**Route:** `/tests/:id/review`

**Purpose:** Review OCR results and correct errors before final save.

### When It Appears
- **Automatically:** After upload if confidence < 80%
- **Manually:** Via "Edit Test Data" button from TestViewer

### Layout: Two-Column Split

#### Left Column (60% width)
- Original JPEG image
- Mantine Image component with zoom capability (click to enlarge in modal)
- Fixed aspect ratio to prevent layout shift
- Confidence score badge overlaid in top-right corner

#### Right Column (40% width)
Scrollable form with two sections:

**Section 1 - Test Metadata:**
- Date picker (Mantine DateInput)
- Location text input
- Device dropdown
- Notes textarea

**Section 2 - Audiogram Data:**
- Tabs: [Left Ear] [Right Ear]
- Table layout with editable cells:
  - Column 1: Frequency (Hz) - read-only labels (64, 125, 250, 500, 1k, 2k, 4k, 8k, 16k)
  - Column 2: Threshold (dB) - NumberInput (0-120, step 5)

**Action Buttons (Bottom):**
- "Accept & Save" (green, primary) - saves changes, navigates to `/tests/:id`
- "Cancel" (gray, outline) - discards changes, navigates back

### Validation Rules
- All frequency fields required
- dB values must be 0-120
- Date cannot be in the future
- Show inline error messages under invalid fields

### Data Flow
1. Load existing test data: `GET /api/tests/:id`
2. User edits values in form
3. Save changes: `PUT /api/tests/:id`
4. Navigate to test viewer: `/tests/:id`

---

## Single Test Viewer

**Route:** `/tests/:id`

**Purpose:** Display detailed view of one test with full audiogram visualization and metadata.

### Layout Sections (Top to Bottom)

#### 1. Header Section
- Test date (large, prominent)
- Location and device (smaller text below date)
- Confidence badge (green/yellow/red based on score)
- Action buttons (right-aligned):
  - "Edit Test Data" → navigates to `/tests/:id/review`
  - "Delete Test" (red, outline, with confirmation dialog)

#### 2. Metadata Card
Grid layout showing:
- Test Date & Time
- Location
- Device
- Source Type (Home/Clinic)
- OCR Confidence Score
- Notes (if any)

#### 3. Audiogram Chart (Main Feature)

**Standard audiogram visualization:**
- Library: Recharts LineChart
- X-axis: Frequencies (64Hz - 16kHz), logarithmic scale
- Y-axis: Hearing loss (0-120 dB), **inverted** (0 at top, 120 at bottom)

**Two lines:**
- Right ear: Red line with circle markers
- Left ear: Blue line with X markers

**Background shaded zones (faint colors):**
- Normal: 0-25 dB (light green)
- Mild: 26-40 dB (yellow)
- Moderate: 41-55 dB (orange)
- Severe/Profound: 56+ dB (red gradient)

**Interactive features:**
- Hover tooltips showing exact values
- Responsive sizing (fills container width)

#### 4. Data Tables (Below Chart)
- Tabs: [Left Ear] [Right Ear]
- Simple table showing Frequency | Threshold for each ear
- Read-only display (click "Edit" button to modify)

### Data Fetching
- React Query: `useQuery(['test', testId])`
- Endpoint: `GET /api/tests/:id`
- Loading skeleton while fetching
- Error state if test not found (404)

---

## All Tests List View

**Route:** `/tests`

**Purpose:** Browse and search through all uploaded tests.

### Layout

#### Header Section
- Page title: "All Tests"
- Total count: "Showing {count} tests"
- Actions (right-aligned):
  - "Upload New Test" button (primary)

#### Tests Table
Mantine Table with sortable columns.

**Columns:**
- Date
- Location
- Source (Home/Clinic)
- Device
- Confidence
- Actions (View button)

**Behavior:**
- Click row to navigate to test viewer (`/tests/:id`)
- Default sort: Date descending (most recent first)
- Pagination if > 50 tests (future enhancement)

### Data Fetching
- React Query: `useQuery(['tests'])`
- Endpoint: `GET /api/tests`
- Sort by date descending

---

## Updated Upload Workflow

### Current Behavior (To Be Replaced)
- Shows results immediately on same page
- Manual review inline with number inputs

### New Upload Workflow

```
1. User selects file, clicks "Process Audiogram"
2. Upload to API, show loading spinner
3. API returns: { test_id, confidence, needs_review, left_ear, right_ear }
4. Frontend decision:

   If confidence >= 0.8:
   - Show success toast: "Test uploaded successfully"
   - Navigate to `/tests/:test_id` (viewer)

   If confidence < 0.8:
   - Navigate to `/tests/:test_id/review` (edit page)

5. User can always edit later via "Edit Test Data" button in viewer
```

### UploadForm Component Changes
- Remove inline result display (table with number inputs)
- After successful upload, use `useNavigate()` to redirect
- Show success/error toast notifications (Mantine notifications)
- Clear file input after successful upload

---

## Backend API Changes

### NEW: Update Test Endpoint

```
PUT /api/tests/:id

Request Body:
{
  "test_date": "2025-01-15",
  "location": "Home",
  "device_name": "Jacoti",
  "notes": "...",
  "left_ear": [
    {"frequency_hz": 125, "threshold_db": 25},
    {"frequency_hz": 250, "threshold_db": 30},
    ...
  ],
  "right_ear": [
    {"frequency_hz": 125, "threshold_db": 30},
    ...
  ]
}

Response:
{
  "id": "test-uuid",
  "test_date": "2025-01-15",
  "location": "Home",
  "device_name": "Jacoti",
  "source_type": "home",
  "left_ear": [...],
  "right_ear": [...],
  "metadata": {...}
}
```

**Purpose:** Save edits from review/edit page.

**Implementation Notes:**
- Validate all fields (same validation as upload)
- Update `hearing_test` table
- Delete existing measurements for this test
- Insert new measurements (deduplicated)
- Return updated test object

### NEW: Delete Test Endpoint

```
DELETE /api/tests/:id

Response:
{
  "success": true
}
```

**Purpose:** Delete button in test viewer.

**Implementation Notes:**
- Delete from `hearing_test` table (cascade to measurements)
- Delete associated image file if exists
- Return 404 if test not found

---

## Frontend File Structure

```
frontend/src/
├── App.tsx (add router, app shell)
├── components/
│   ├── AppShell.tsx (new - navbar + shell wrapper)
│   ├── Navigation.tsx (new - nav links)
│   ├── UploadForm.tsx (modify - remove inline results, add navigation)
│   ├── AudiogramChart.tsx (new - Recharts component)
│   └── TestDataTable.tsx (new - reusable frequency/threshold table)
├── pages/
│   ├── Dashboard.tsx (new)
│   ├── TestList.tsx (new)
│   ├── TestViewer.tsx (new)
│   └── TestReviewEdit.tsx (new)
└── lib/
    └── api.ts (add updateTest, deleteTest functions)
```

---

## Dependencies to Install

### Frontend
```bash
npm install react-router-dom recharts
npm install --save-dev @types/react-router-dom
```

---

## Implementation Order

### Phase 1: Navigation Foundation
1. Install dependencies
2. Create AppShell component with navbar
3. Add React Router to App.tsx
4. Create placeholder pages (Dashboard, TestList, TestViewer, TestReviewEdit)
5. Verify navigation works between all routes

### Phase 2: Backend API Extensions
1. Implement `PUT /api/tests/:id` endpoint
2. Implement `DELETE /api/tests/:id` endpoint
3. Test endpoints with curl/Postman

### Phase 3: Dashboard
1. Create Dashboard component
2. Implement stats cards
3. Implement latest test card (without chart initially)
4. Implement recent tests table
5. Add empty state handling

### Phase 4: Test List
1. Create TestList component
2. Implement table with all columns
3. Add click handlers for navigation
4. Connect to `/api/tests` endpoint

### Phase 5: Test Viewer
1. Create TestViewer component
2. Implement header with metadata
3. Create AudiogramChart component (Recharts)
4. Add data tables below chart
5. Implement edit/delete buttons

### Phase 6: Review/Edit Page
1. Create TestReviewEdit component
2. Implement two-column layout
3. Add image display with zoom
4. Create editable form (metadata + measurements)
5. Connect to PUT endpoint for saving

### Phase 7: Upload Integration
1. Modify UploadForm to navigate after upload
2. Implement confidence check (>= 80% vs < 80%)
3. Add toast notifications
4. Remove inline result display

### Phase 8: Polish & Testing
1. Add loading skeletons
2. Add error states
3. Test all navigation flows
4. Test with real data
5. Responsive design adjustments

---

## Success Criteria

This design succeeds if:

1. Users can navigate between all views using the navbar
2. Dashboard shows accurate stats and latest test
3. Upload redirects to appropriate page based on confidence
4. Low-confidence uploads allow review/editing before final save
5. Test viewer displays audiogram chart correctly (inverted Y-axis, proper colors)
6. All tests can be viewed in a sortable table
7. Tests can be edited and deleted from the viewer
8. Navigation feels smooth and intuitive

---

## Future Enhancements

Beyond this initial navigation implementation:

1. Add search/filter to test list (by date range, location, confidence)
2. Add comparison mode (select multiple tests, view side-by-side)
3. Add trend charts (Mode 2 from original design doc)
4. Add calendar heatmap view (Mode 3)
5. Add animation timeline (Mode 4)
6. Add PDF export functionality
7. Add batch upload for historical tests

---

## Conclusion

This design establishes the core navigation structure and views needed for a functional hearing test tracker. By implementing an app shell with clear navigation, a comprehensive dashboard, detailed test viewer, and review/edit capabilities, users can effectively manage and analyze their hearing test data.

The phased implementation approach ensures steady progress with working features at each step. Starting with navigation foundation and backend API, then building out each view systematically, minimizes risk and allows for early testing of the complete user flow.

Next step: Create detailed implementation plan with specific tasks and code examples for each phase.
