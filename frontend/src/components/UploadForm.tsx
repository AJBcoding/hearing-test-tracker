import { useState } from 'react'
import { Button, FileInput, Stack, Alert, Table } from '@mantine/core'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadAudiogram, type UploadResponse } from '../lib/api'

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<UploadResponse | null>(null)
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: uploadAudiogram,
    onSuccess: (data) => {
      setResult(data)
      queryClient.invalidateQueries({ queryKey: ['tests'] })
    }
  })

  const handleUpload = () => {
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  return (
    <Stack>
      <FileInput
        label="Upload Audiogram"
        placeholder="Select JPEG image"
        accept="image/jpeg,image/jpg"
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

      {result && (
        <>
          <Alert
            color={result.needs_review ? 'yellow' : 'green'}
            title="Upload Successful"
          >
            Confidence: {(result.confidence * 100).toFixed(0)}%
            {result.needs_review && ' - Manual review recommended'}
          </Alert>

          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Frequency (Hz)</Table.Th>
                <Table.Th>Left Ear (dB)</Table.Th>
                <Table.Th>Right Ear (dB)</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {result.left_ear.map((left, idx) => {
                const right = result.right_ear[idx]
                return (
                  <Table.Tr key={left.frequency_hz}>
                    <Table.Td>{left.frequency_hz}</Table.Td>
                    <Table.Td>{left.threshold_db.toFixed(1)}</Table.Td>
                    <Table.Td>{right?.threshold_db.toFixed(1) || '-'}</Table.Td>
                  </Table.Tr>
                )
              })}
            </Table.Tbody>
          </Table>
        </>
      )}
    </Stack>
  )
}
