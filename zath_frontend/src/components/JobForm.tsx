"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
} from "@mui/material";
import { api, JobCreate } from "@/lib/api";

const TASK_TYPES = [
  { value: "email_send", label: "Send Email" },
  { value: "data_process", label: "Process Data" },
  { value: "webhook_call", label: "Webhook Call" },
  { value: "file_upload", label: "File Upload" },
  { value: "report_generate", label: "Generate Report" },
  { value: "custom_task", label: "Custom Task" },
];

export function JobForm() {
  const [taskType, setTaskType] = useState("");
  const [payload, setPayload] = useState('{\n  "message": "Hello World"\n}');
  const [callbackUrl, setCallbackUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [createdJob, setCreatedJob] = useState<any>(null);

  // Check if callback URL needs protocol
  const needsProtocol = callbackUrl && !callbackUrl.match(/^https?:\/\//);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      // Parse payload JSON
      let parsedPayload;
      try {
        parsedPayload = JSON.parse(payload);
      } catch (err) {
        setError("Invalid JSON payload. Please check the format.");
        setLoading(false);
        return;
      }

      // Process callback URL - add https:// if no protocol provided
      let processedCallbackUrl = callbackUrl;
      if (callbackUrl && !callbackUrl.match(/^https?:\/\//)) {
        processedCallbackUrl = `https://${callbackUrl}`;
      }

      const jobData: JobCreate = {
        task_type: taskType,
        payload: parsedPayload,
        ...(processedCallbackUrl && { callback_url: processedCallbackUrl }),
      };

      const job = await api.createJob(jobData);
      setCreatedJob(job);
      setSuccess(`Job created successfully! Job ID: ${job.job_id}`);

      // Reset form
      setTaskType("");
      setPayload('{\n  "message": "Hello World"\n}');
      setCallbackUrl("");
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Failed to create job. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card sx={{ maxWidth: 600, mx: "auto", mt: 4 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Create New Job
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Create a new asynchronous job in the ZATH system.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Task Type</InputLabel>
            <Select
              value={taskType}
              label="Task Type"
              onChange={(e) => setTaskType(e.target.value)}
              required
              disabled={loading}
            >
              {TASK_TYPES.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  {type.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Payload (JSON)"
            multiline
            rows={6}
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
            required
            sx={{ mb: 2 }}
            disabled={loading}
            helperText="Enter JSON payload for the job"
          />

          <TextField
            fullWidth
            label="Callback URL (Optional)"
            value={callbackUrl}
            onChange={(e) => setCallbackUrl(e.target.value)}
            sx={{ mb: 2 }}
            disabled={loading}
            helperText={
              needsProtocol
                ? `Will be sent as: https://${callbackUrl}`
                : "Webhook URL for job completion notifications (e.g., https://webhook.site/abc123 or just google.com)"
            }
            color={needsProtocol ? "warning" : "primary"}
          />

          <Button
            type="submit"
            variant="contained"
            fullWidth
            disabled={loading || !taskType || !payload}
            sx={{ mb: 2 }}
          >
            {loading ? "Creating Job..." : "Create Job"}
          </Button>
        </Box>

        {createdJob && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Created Job:
            </Typography>
            <Chip
              label={`Job ID: ${createdJob.job_id}`}
              variant="outlined"
              sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}
            />
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Status: {createdJob.status} | Created:{" "}
              {new Date(createdJob.created_at).toLocaleString()}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
