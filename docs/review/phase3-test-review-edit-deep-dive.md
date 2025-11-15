# Deep Dive: TestReviewEdit Flow

**Flow:** Review and Edit OCR-Extracted Test Data
**Files:**
- Frontend: `frontend/src/pages/TestReviewEdit.tsx`
- Backend: `backend/api/routes.py:270-337` (update_test endpoint)
- API Client: `frontend/src/lib/api.ts:78-88`

**Severity Summary:** 2 High + 3 Medium + 1 Low = 6 total issues

---

## Error Handling & Data Integrity

### Issue 1: No Error Handling on Update Mutation

**Severity:** 🔴 CRITICAL (High)
**Location:** `frontend/src/pages/TestReviewEdit.tsx:37-51`
**Category:** Error Handling / Data Loss

**Description:**

The update mutation has no `onError` handler. If the update fails (network error, validation error, server error), the user doesn't see an error message and has no way to retry. Changes appear to be lost silently.

**Current Code:**

```tsx
const updateMutation = useMutation({
  mutationFn: () => updateTest(id!, {
    test_date: testDate!.toISOString().split('T')[0],
    location,
    device_name: device,
    notes,
    left_ear: leftEar,
    right_ear: rightEar
  }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['test', id] })
    queryClient.invalidateQueries({ queryKey: ['tests'] })
    navigate(`/tests/${id}`)
  }
  // Missing onError handler!
})
```

**Impact:**
- Silent failures - user doesn't know update failed
- Data loss - user thinks changes were saved
- No retry mechanism
- Difficult to debug issues
- Poor user experience

**Alternatives:**

**Option 1: Comprehensive Error Handling with Retry** ⭐ Recommended

```tsx
import { notifications } from '@mantine/notifications'
import { modals } from '@mantine/modals'

const updateMutation = useMutation({
  mutationFn: () => updateTest(id!, {
    test_date: testDate!.toISOString().split('T')[0],
    location,
    device_name: device,
    notes,
    left_ear: leftEar,
    right_ear: rightEar
  }),
  onSuccess: () => {
    // Invalidate queries to refresh data
    queryClient.invalidateQueries({ queryKey: ['test', id] })
    queryClient.invalidateQueries({ queryKey: ['tests'] })

    // Show success notification
    notifications.show({
      title: 'Test Updated',
      message: 'Your changes have been saved successfully',
      color: 'green'
    })

    // Navigate back to test view
    navigate(`/tests/${id}`)
  },
  onError: (error) => {
    // Log error for debugging
    console.error('Update failed:', error)

    // Extract user-friendly error message
    const errorMessage = error instanceof Error
      ? error.message
      : 'An unexpected error occurred while saving your changes'

    // Show error notification with retry option
    notifications.show({
      title: 'Update Failed',
      message: errorMessage,
      color: 'red',
      autoClose: false, // Keep it visible
      withCloseButton: true
    })

    // Optional: Show modal for retry
    modals.openConfirmModal({
      title: 'Update Failed',
      children: (
        <>
          <p>Your changes could not be saved:</p>
          <p><strong>{errorMessage}</strong></p>
          <p>Would you like to try again?</p>
        </>
      ),
      labels: { confirm: 'Retry', cancel: 'Cancel' },
      confirmProps: { color: 'blue' },
      onConfirm: () => updateMutation.mutate()
    })
  }
})
```

- **Pro:** Clear error feedback to user
- **Pro:** Retry mechanism built in
- **Pro:** Persistent notification (user won't miss it)
- **Con:** Requires modal library

**Option 2: Simple Error Display with Manual Retry**

```tsx
const updateMutation = useMutation({
  mutationFn: () => updateTest(id!, { /* ... */ }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['test', id] })
    queryClient.invalidateQueries({ queryKey: ['tests'] })
    notifications.show({
      title: 'Success',
      message: 'Test updated successfully',
      color: 'green'
    })
    navigate(`/tests/${id}`)
  },
  onError: (error) => {
    notifications.show({
      title: 'Update Failed',
      message: error instanceof Error ? error.message : 'Failed to update test',
      color: 'red'
    })
  }
})

// Show error in UI (not just notification)
{updateMutation.isError && (
  <Alert color="red" title="Update Failed" mb="md">
    {updateMutation.error instanceof Error
      ? updateMutation.error.message
      : 'An error occurred. Please try again.'}
  </Alert>
)}
```

- **Pro:** Simple implementation
- **Pro:** Error visible in UI
- **Con:** User must manually retry (click save again)

**Option 3: Optimistic Update with Rollback**

```tsx
const updateMutation = useMutation({
  mutationFn: (data) => updateTest(id!, data),

  // Optimistic update - update UI immediately
  onMutate: async (newData) => {
    // Cancel any outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['test', id] })

    // Snapshot previous value
    const previousTest = queryClient.getQueryData(['test', id])

    // Optimistically update to the new value
    queryClient.setQueryData(['test', id], (old: any) => ({
      ...old,
      test_date: newData.test_date,
      location: newData.location,
      left_ear: newData.left_ear,
      right_ear: newData.right_ear,
      metadata: {
        ...old.metadata,
        device: newData.device_name,
        notes: newData.notes
      }
    }))

    // Return context with previous value
    return { previousTest }
  },

  onError: (error, variables, context) => {
    // Rollback to previous value
    queryClient.setQueryData(['test', id], context?.previousTest)

    notifications.show({
      title: 'Update Failed',
      message: 'Changes have been reverted',
      color: 'red'
    })
  },

  onSuccess: () => {
    notifications.show({
      title: 'Test Updated',
      message: 'Your changes have been saved',
      color: 'green'
    })
    navigate(`/tests/${id}`)
  },

  // Always refetch after error or success
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['test', id] })
  }
})
```

- **Pro:** Instant UI update (feels fast)
- **Pro:** Automatic rollback on failure
- **Con:** More complex implementation
- **Con:** Can be confusing if network is slow

**Recommendation:** Option 1 (Error Handling with Retry) for reliability. Option 3 (Optimistic Update) if you want instant UI feedback.

---

### Issue 2: Unsafe Type Assertion on testDate

**Severity:** 🔴 CRITICAL (High)
**Location:** `frontend/src/pages/TestReviewEdit.tsx:39`
**Category:** Type Safety / Runtime Error

**Description:**

Uses non-null assertion `testDate!.toISOString()` which will throw if testDate is null. User can click "Accept & Save" before test loads or if date is cleared, causing app crash.

**Current Code:**

```tsx
const updateMutation = useMutation({
  mutationFn: () => updateTest(id!, {
    test_date: testDate!.toISOString().split('T')[0],  // Crashes if testDate is null!
    // ...
  }),
  // ...
})
```

**Impact:**
- Application crash if testDate is null
- Poor user experience (white screen)
- Data loss (form state lost on crash)
- Can occur if:
  - User clears date field
  - Test data hasn't loaded yet
  - Invalid date in original data

**Alternatives:**

**Option 1: Validate Before Submitting** ⭐ Recommended

```tsx
const [validationErrors, setValidationErrors] = useState<string[]>([])

const handleSave = () => {
  // Validate before submitting
  const errors: string[] = []

  if (!testDate) {
    errors.push('Test date is required')
  }

  if (leftEar.length === 0) {
    errors.push('Left ear measurements are required')
  }

  if (rightEar.length === 0) {
    errors.push('Right ear measurements are required')
  }

  // Check for invalid threshold values
  const invalidThresholds = [...leftEar, ...rightEar].filter(
    m => m.threshold_db < 0 || m.threshold_db > 120
  )
  if (invalidThresholds.length > 0) {
    errors.push('Threshold values must be between 0 and 120 dB')
  }

  if (errors.length > 0) {
    setValidationErrors(errors)
    notifications.show({
      title: 'Validation Failed',
      message: 'Please fix the errors before saving',
      color: 'red'
    })
    return
  }

  // Clear errors and submit
  setValidationErrors([])
  updateMutation.mutate()
}

const updateMutation = useMutation({
  mutationFn: () => updateTest(id!, {
    test_date: testDate.toISOString().split('T')[0], // Safe now (validated above)
    location,
    device_name: device,
    notes,
    left_ear: leftEar,
    right_ear: rightEar
  }),
  // ... handlers
})

return (
  <Container size="xl" py="xl">
    {/* ... */}

    {validationErrors.length > 0 && (
      <Alert color="red" title="Please fix the following errors:" mb="md">
        <ul>
          {validationErrors.map((error, idx) => (
            <li key={idx}>{error}</li>
          ))}
        </ul>
      </Alert>
    )}

    {/* ... */}

    <Button
      onClick={handleSave}  // Use validation handler
      loading={updateMutation.isPending}
      disabled={!testDate}  // Disable if required fields missing
    >
      Accept & Save
    </Button>
  </Container>
)
```

- **Pro:** Prevents invalid submissions
- **Pro:** Clear error messages
- **Pro:** User-friendly validation
- **Con:** More code

**Option 2: Safe Null Handling with Default**

```tsx
const updateMutation = useMutation({
  mutationFn: () => {
    // Provide default if testDate is null
    const dateToSave = testDate
      ? testDate.toISOString().split('T')[0]
      : new Date().toISOString().split('T')[0] // Default to today

    return updateTest(id!, {
      test_date: dateToSave,
      // ...
    })
  },
  // ...
})
```

- **Pro:** Never crashes
- **Pro:** Simple
- **Con:** Silently uses default (user may not notice)
- **Con:** May save incorrect data

**Option 3: Form Library with Built-in Validation (react-hook-form)**

```tsx
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

// Define validation schema
const testSchema = z.object({
  test_date: z.date({ required_error: 'Test date is required' }),
  location: z.string().optional(),
  device: z.string().optional(),
  notes: z.string().optional(),
  left_ear: z.array(z.object({
    frequency_hz: z.number(),
    threshold_db: z.number().min(0).max(120)
  })).min(1, 'Left ear measurements required'),
  right_ear: z.array(z.object({
    frequency_hz: z.number(),
    threshold_db: z.number().min(0).max(120)
  })).min(1, 'Right ear measurements required')
})

type TestFormData = z.infer<typeof testSchema>

export function TestReviewEdit() {
  const { id } = useParams<{ id: string }>()

  const { control, handleSubmit, formState: { errors }, setValue } = useForm<TestFormData>({
    resolver: zodResolver(testSchema)
  })

  // ... data fetching

  useEffect(() => {
    if (test) {
      setValue('test_date', new Date(test.test_date))
      setValue('location', test.location || '')
      setValue('left_ear', test.left_ear)
      setValue('right_ear', test.right_ear)
    }
  }, [test, setValue])

  const onSubmit = (data: TestFormData) => {
    updateMutation.mutate({
      test_date: data.test_date.toISOString().split('T')[0], // Type-safe!
      location: data.location,
      device_name: data.device,
      notes: data.notes,
      left_ear: data.left_ear,
      right_ear: data.right_ear
    })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Controller
        name="test_date"
        control={control}
        render={({ field }) => (
          <DateInput
            {...field}
            label="Test Date"
            error={errors.test_date?.message}
          />
        )}
      />

      {/* ... other fields */}

      <Button type="submit" loading={updateMutation.isPending}>
        Accept & Save
      </Button>
    </form>
  )
}
```

- **Pro:** Type-safe, compile-time checked
- **Pro:** Automatic validation
- **Pro:** Clean code with less boilerplate
- **Con:** Additional dependencies (react-hook-form, zod)
- **Con:** Learning curve

**Recommendation:** Option 1 (Manual Validation) for immediate fix. Option 3 (Form Library) for robust long-term solution.

---

## User Experience & Data Safety

### Issue 3: No Dirty State Tracking (Unsaved Changes)

**Severity:** 🟡 MEDIUM
**Location:** `frontend/src/pages/TestReviewEdit.tsx:198-200`
**Category:** Data Loss Prevention / UX

**Description:**

User can click "Cancel" or navigate away without warning about unsaved changes. If user spent 10 minutes editing measurements, all changes are lost silently.

**Current Code:**

```tsx
<Button variant="outline" onClick={() => navigate(`/tests/${id}`)}>
  Cancel  {/* No warning about unsaved changes! */}
</Button>
```

**Impact:**
- Accidental data loss
- Frustrating user experience
- No recovery option
- Especially problematic for long editing sessions

**Alternatives:**

**Option 1: Track Dirty State with Confirmation Modal** ⭐ Recommended

```tsx
import { useMemo, useCallback } from 'react'
import { modals } from '@mantine/modals'

export function TestReviewEdit() {
  // ... existing state

  // Track if form is dirty (has unsaved changes)
  const isDirty = useMemo(() => {
    if (!test) return false

    // Check if any field changed
    const dateChanged = testDate?.toISOString().split('T')[0] !==
                        new Date(test.test_date).toISOString().split('T')[0]
    const locationChanged = location !== (test.location || '')
    const deviceChanged = device !== (test.metadata?.device || '')
    const notesChanged = notes !== (test.metadata?.notes || '')

    // Check if measurements changed
    const leftEarChanged = JSON.stringify(leftEar) !== JSON.stringify(test.left_ear)
    const rightEarChanged = JSON.stringify(rightEar) !== JSON.stringify(test.right_ear)

    return dateChanged || locationChanged || deviceChanged || notesChanged ||
           leftEarChanged || rightEarChanged
  }, [test, testDate, location, device, notes, leftEar, rightEar])

  const handleCancel = useCallback(() => {
    if (isDirty) {
      modals.openConfirmModal({
        title: 'Unsaved Changes',
        children: (
          <p>
            You have unsaved changes. Are you sure you want to leave?
            Your changes will be lost.
          </p>
        ),
        labels: { confirm: 'Discard Changes', cancel: 'Keep Editing' },
        confirmProps: { color: 'red' },
        onConfirm: () => navigate(`/tests/${id}`)
      })
    } else {
      navigate(`/tests/${id}`)
    }
  }, [isDirty, navigate, id])

  // Warn on browser navigation (back button, refresh, close tab)
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault()
        e.returnValue = '' // Chrome requires returnValue to be set
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [isDirty])

  return (
    <Container size="xl" py="xl">
      {/* ... */}

      <Group justify="space-between" mb="md">
        {isDirty && (
          <Badge color="yellow" size="lg">
            Unsaved Changes
          </Badge>
        )}
      </Group>

      {/* ... */}

      <Button variant="outline" onClick={handleCancel}>
        Cancel
      </Button>
    </Container>
  )
}
```

- **Pro:** Prevents accidental data loss
- **Pro:** Clear visual indicator (badge)
- **Pro:** Warns on browser navigation too
- **Con:** More complex implementation

**Option 2: Auto-Save Draft**

```tsx
import { useDebounce } from 'use-debounce'

export function TestReviewEdit() {
  // ... existing state

  // Debounce form state changes
  const [debouncedFormState] = useDebounce(
    { testDate, location, device, notes, leftEar, rightEar },
    2000 // Save after 2 seconds of inactivity
  )

  // Auto-save to localStorage
  useEffect(() => {
    if (test && id) {
      const draft = {
        test_id: id,
        testDate: debouncedFormState.testDate?.toISOString(),
        location: debouncedFormState.location,
        device: debouncedFormState.device,
        notes: debouncedFormState.notes,
        leftEar: debouncedFormState.leftEar,
        rightEar: debouncedFormState.rightEar,
        savedAt: new Date().toISOString()
      }

      localStorage.setItem(`draft_test_${id}`, JSON.stringify(draft))
    }
  }, [debouncedFormState, test, id])

  // Load draft on mount
  useEffect(() => {
    if (id && !test) {
      const draftKey = `draft_test_${id}`
      const savedDraft = localStorage.getItem(draftKey)

      if (savedDraft) {
        const draft = JSON.parse(savedDraft)

        modals.openConfirmModal({
          title: 'Draft Found',
          children: (
            <p>
              A draft from {new Date(draft.savedAt).toLocaleString()} was found.
              Would you like to restore it?
            </p>
          ),
          labels: { confirm: 'Restore Draft', cancel: 'Discard' },
          onConfirm: () => {
            setTestDate(draft.testDate ? new Date(draft.testDate) : null)
            setLocation(draft.location || '')
            setDevice(draft.device || '')
            setNotes(draft.notes || '')
            setLeftEar(draft.leftEar || [])
            setRightEar(draft.rightEar || [])
          },
          onCancel: () => {
            localStorage.removeItem(draftKey)
          }
        })
      }
    }
  }, [id, test])

  // Clear draft on successful save
  const updateMutation = useMutation({
    mutationFn: () => updateTest(/* ... */),
    onSuccess: () => {
      localStorage.removeItem(`draft_test_${id}`)
      // ...
    }
  })
}
```

- **Pro:** Never loses work (auto-saved)
- **Pro:** Recovers from crashes/accidental navigation
- **Con:** Complex implementation
- **Con:** localStorage can fill up

**Option 3: Simple Confirm Before Navigation (React Router)**

```tsx
import { useBlocker } from 'react-router-dom'

export function TestReviewEdit() {
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  // Block navigation if unsaved changes
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      hasUnsavedChanges &&
      currentLocation.pathname !== nextLocation.pathname
  )

  useEffect(() => {
    if (blocker.state === 'blocked') {
      const proceed = window.confirm(
        'You have unsaved changes. Are you sure you want to leave?'
      )
      if (proceed) {
        blocker.proceed()
      } else {
        blocker.reset()
      }
    }
  }, [blocker])

  // Track changes
  useEffect(() => {
    // Set to true when any field changes
    setHasUnsavedChanges(true)
  }, [testDate, location, device, notes, leftEar, rightEar])

  // Clear on save
  const updateMutation = useMutation({
    mutationFn: () => updateTest(/* ... */),
    onSuccess: () => {
      setHasUnsavedChanges(false)
      // ...
    }
  })
}
```

- **Pro:** Built-in to React Router
- **Pro:** Simple implementation
- **Con:** Uses native confirm (not pretty)
- **Con:** Doesn't track specific changes

**Recommendation:** Option 1 (Dirty Tracking with Modal) for best UX. Option 2 (Auto-Save) if you want ultimate data safety.

---

### Issue 4: No Client-Side Validation

**Severity:** 🟡 MEDIUM
**Location:** `frontend/src/pages/TestReviewEdit.tsx:38-45`
**Category:** UX / Data Quality

**Description:**

Form submits without validating required fields or value ranges. User can submit empty date, invalid thresholds (e.g., 999 dB), resulting in wasted API calls and server-side errors.

**Solution:**

Covered by **Issue 2 (Option 1 - Validation)** above. Implement validation before submission.

---

### Issue 5: No Concurrent Edit Detection

**Severity:** 🟡 MEDIUM
**Location:** `frontend/src/pages/TestReviewEdit.tsx:37-51`
**Category:** Data Integrity

**Description:**

If two users edit the same test simultaneously, last write wins with no conflict detection. User A's changes can be silently overwritten by User B.

**Solution:**

This requires backend support (covered in **Backend CRUD Routes Deep Dive, Issue 6 - Optimistic Locking**). Frontend implementation:

```tsx
import { useQuery, useMutation } from '@tanstack/react-query'

export function TestReviewEdit() {
  const { data: test } = useQuery({
    queryKey: ['test', id],
    queryFn: () => getTest(id!),
    // Refetch on window focus to detect changes
    refetchOnWindowFocus: true
  })

  // Store the modified_at timestamp we loaded
  const [loadedTimestamp, setLoadedTimestamp] = useState<string | null>(null)

  useEffect(() => {
    if (test?.metadata?.modified_at) {
      setLoadedTimestamp(test.metadata.modified_at)
    }
  }, [test])

  const updateMutation = useMutation({
    mutationFn: () => updateTest(id!, {
      test_date: testDate!.toISOString().split('T')[0],
      location,
      device_name: device,
      notes,
      left_ear: leftEar,
      right_ear: rightEar,
      modified_at: loadedTimestamp // Send timestamp for conflict detection
    }),
    onError: (error: any) => {
      // Check if it's a conflict error (409)
      if (error.response?.status === 409) {
        modals.openConfirmModal({
          title: 'Conflict Detected',
          children: (
            <>
              <p>This test was modified by another user while you were editing.</p>
              <p>Would you like to:</p>
              <ul>
                <li><strong>Reload:</strong> Discard your changes and see the latest version</li>
                <li><strong>Force Save:</strong> Overwrite with your changes (not recommended)</li>
              </ul>
            </>
          ),
          labels: { confirm: 'Reload', cancel: 'Force Save' },
          onConfirm: () => {
            queryClient.invalidateQueries({ queryKey: ['test', id] })
          },
          onCancel: () => {
            // Force save by retrying without timestamp check
            // (requires backend to support force flag)
          }
        })
      } else {
        // Handle other errors normally
        notifications.show({
          title: 'Update Failed',
          message: error.message,
          color: 'red'
        })
      }
    }
  })
}
```

---

## Summary & Recommendations

### Critical Priority (Implement First)

1. **Add Error Handling** (Issue 1)
   - onError handler with notifications
   - Retry mechanism
   - Clear error messages to user

2. **Fix Unsafe Type Assertion** (Issue 2)
   - Validate testDate before submission
   - Show validation errors clearly
   - Disable save button if invalid

### High Priority (Prevent Data Loss)

3. **Add Dirty State Tracking** (Issue 3)
   - Track unsaved changes
   - Confirm before navigation
   - Warn on browser close/refresh
   - Visual indicator for unsaved state

4. **Add Client-Side Validation** (Issue 4)
   - Validate required fields
   - Check value ranges (0-120 dB)
   - Clear error messages

### Medium Priority (Nice to Have)

5. **Add Concurrent Edit Detection** (Issue 5)
   - Requires backend support (modified_at timestamp)
   - Frontend conflict resolution UI

### Code Changes Summary

**Files to Modify:**
- `frontend/src/pages/TestReviewEdit.tsx` - Add error handling, validation, dirty tracking
- `frontend/src/lib/api.ts` - Add modified_at to update payload (for Issue 5)

**New Dependencies (Optional):**
- `react-hook-form` + `zod` for robust validation
- `@mantine/modals` for confirmation dialogs

**Estimated Effort:** 3-4 hours for critical + high priority issues
