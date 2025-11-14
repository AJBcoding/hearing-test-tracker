import { useState } from 'react'
import { Button, FileInput, Stack, Alert, Table, NumberInput, Group } from '@mantine/core'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadAudiogram, type UploadResponse, type AudiogramMeasurement } from '../lib/api'

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<UploadResponse | null>(null)
  const [editedLeftEar, setEditedLeftEar] = useState<AudiogramMeasurement[]>([])
  const [editedRightEar, setEditedRightEar] = useState<AudiogramMeasurement[]>([])
  const [isEditing, setIsEditing] = useState(false)
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: uploadAudiogram,
    onSuccess: (data) => {
      setResult(data)
      setEditedLeftEar(data.left_ear)
      setEditedRightEar(data.right_ear)
      setIsEditing(data.needs_review)
      queryClient.invalidateQueries({ queryKey: ['tests'] })
    }
  })

  const handleUpload = () => {
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  const handleConfirm = () => {
    setIsEditing(false)
    // TODO: Send updated values to backend if they were edited
  }

  const updateLeftEar = (index: number, value: number) => {
    const updated = [...editedLeftEar]
    updated[index] = { ...updated[index], threshold_db: value }
    setEditedLeftEar(updated)
  }

  const updateRightEar = (index: number, value: number) => {
    const updated = [...editedRightEar]
    updated[index] = { ...updated[index], threshold_db: value }
    setEditedRightEar(updated)
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
            color={isEditing ? 'yellow' : 'green'}
            title={isEditing ? 'Manual Review Required' : 'Upload Successful'}
          >
            Confidence: {(result.confidence * 100).toFixed(0)}%
            {isEditing && ' - Please review and correct values below'}
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
              {editedLeftEar.map((left, idx) => {
                const right = editedRightEar[idx]
                return (
                  <Table.Tr key={left.frequency_hz}>
                    <Table.Td>{left.frequency_hz}</Table.Td>
                    <Table.Td>
                      {isEditing ? (
                        <NumberInput
                          value={left.threshold_db}
                          onChange={(val) => updateLeftEar(idx, val as number)}
                          min={0}
                          max={120}
                          step={5}
                          size="xs"
                        />
                      ) : (
                        left.threshold_db.toFixed(1)
                      )}
                    </Table.Td>
                    <Table.Td>
                      {right ? (
                        isEditing ? (
                          <NumberInput
                            value={right.threshold_db}
                            onChange={(val) => updateRightEar(idx, val as number)}
                            min={0}
                            max={120}
                            step={5}
                            size="xs"
                          />
                        ) : (
                          right.threshold_db.toFixed(1)
                        )
                      ) : '-'}
                    </Table.Td>
                  </Table.Tr>
                )
              })}
            </Table.Tbody>
          </Table>

          {isEditing && (
            <Group justify="flex-end">
              <Button onClick={handleConfirm} color="green">
                Confirm & Save Results
              </Button>
            </Group>
          )}
        </>
      )}
    </Stack>
  )
}
