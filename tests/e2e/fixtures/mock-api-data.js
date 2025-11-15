/**
 * Mock API response data for E2E tests
 * These fixtures allow tests to run without a backend server
 */

/**
 * Empty tests array (for initial dashboard empty state)
 */
export const emptyTests = [];

/**
 * Sample hearing test data
 */
export const sampleTests = [
  {
    id: 1,
    test_date: '2025-11-10',
    location: 'City Audiology Center',
    source_type: 'upload',
    confidence: 0.95,
    created_at: '2025-11-10T10:30:00Z',
    updated_at: '2025-11-10T10:30:00Z'
  },
  {
    id: 2,
    test_date: '2025-10-15',
    location: 'University Hospital',
    source_type: 'upload',
    confidence: 0.88,
    created_at: '2025-10-15T14:20:00Z',
    updated_at: '2025-10-15T14:20:00Z'
  },
  {
    id: 3,
    test_date: '2025-09-20',
    location: 'Metro Hearing Clinic',
    source_type: 'bulk_upload',
    confidence: 0.92,
    created_at: '2025-09-20T09:15:00Z',
    updated_at: '2025-09-20T09:15:00Z'
  },
  {
    id: 4,
    test_date: '2025-08-05',
    location: 'City Audiology Center',
    source_type: 'upload',
    confidence: 0.76,
    created_at: '2025-08-05T16:45:00Z',
    updated_at: '2025-08-05T16:45:00Z'
  },
  {
    id: 5,
    test_date: '2025-07-12',
    location: 'Private Practice',
    source_type: 'upload',
    confidence: 0.84,
    created_at: '2025-07-12T11:00:00Z',
    updated_at: '2025-07-12T11:00:00Z'
  }
];

/**
 * Sample individual test details
 */
export const sampleTestDetails = {
  id: 1,
  test_date: '2025-11-10',
  location: 'City Audiology Center',
  source_type: 'upload',
  confidence: 0.95,
  created_at: '2025-11-10T10:30:00Z',
  updated_at: '2025-11-10T10:30:00Z',
  frequencies: {
    left: {
      250: 15,
      500: 20,
      1000: 25,
      2000: 30,
      4000: 35,
      8000: 40
    },
    right: {
      250: 10,
      500: 15,
      1000: 20,
      2000: 25,
      4000: 30,
      8000: 35
    }
  },
  notes: 'Sample audiogram test data',
  original_image_url: '/uploads/test-1.jpg'
};

/**
 * Mock upload response (high confidence)
 */
export const uploadSuccessResponse = {
  test_id: 6,
  confidence: 0.92,
  message: 'Audiogram processed successfully'
};

/**
 * Mock upload response (low confidence, needs review)
 */
export const uploadReviewResponse = {
  test_id: 7,
  confidence: 0.65,
  message: 'Audiogram processed but requires review'
};

/**
 * Mock upload error response
 */
export const uploadErrorResponse = {
  error: 'Invalid file format',
  message: 'Only JPEG and PNG files are supported'
};
