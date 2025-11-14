import { useState } from 'react'
import { Button, FileInput, Stack, Alert, Paper, Title } from '@mantine/core'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { notifications } from '@mantine/notifications'
import { uploadAudiogram } from '../lib/api'

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: uploadAudiogram,
    onSuccess: (data) => {
      if (data.confidence >= 0.8) {
        notifications.show({
          title: 'Upload Successful',
          message: `Test uploaded with ${(data.confidence * 100).toFixed(0)}% confidence`,
          color: 'green'
        })
        navigate(`/tests/${data.test_id}`)
      } else {
        navigate(`/tests/${data.test_id}/review`)
      }
      queryClient.invalidateQueries({ queryKey: ['tests'] })
    }
  })

  const handleUpload = () => {
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  return (
    <Paper p="md" withBorder>
      <Stack>
        <Title order={3}>Upload Single Audiogram</Title>

        <FileInput
          label="Select Audiogram Image"
          placeholder="Click to select a JPEG file"
          accept="image/jpeg,image/jpg,image/png"
          value={file}
          onChange={setFile}
        />

        <Button
          onClick={handleUpload}
          disabled={!file || uploadMutation.isPending}
          loading={uploadMutation.isPending}
        >
          Process Audiogram
        </Button>

        {uploadMutation.isError && (
          <Alert color="red" title="Upload Failed">
            {uploadMutation.error.message}
          </Alert>
        )}
      </Stack>
    </Paper>
  )
}
