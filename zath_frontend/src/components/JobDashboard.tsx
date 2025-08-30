"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Alert,
  Pagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Tooltip,
  CircularProgress,
} from "@mui/material";
import {
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
} from "@mui/icons-material";
import { api, JobListItem, JobStatus } from "@/lib/api";

const getStatusColor = (status: string) => {
  switch (status) {
    case "queued":
      return "default";
    case "in_progress":
      return "warning";
    case "completed":
      return "success";
    case "failed":
      return "error";
    default:
      return "default";
  }
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

const truncateId = (id: string) => {
  return `${id.substring(0, 8)}...`;
};

export function JobDashboard() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);

  // Filters
  const [statusFilter, setStatusFilter] = useState("");
  const [taskTypeFilter, setTaskTypeFilter] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  // Selected job for details
  const [selectedJob, setSelectedJob] = useState<JobStatus | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);

  // Auto-refresh
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadJobs = async () => {
    try {
      setLoading(true);
      setError("");

      const params: any = {
        page,
        limit,
      };

      if (statusFilter) params.status = statusFilter;
      if (taskTypeFilter) params.task_type = taskTypeFilter;

      const response = await api.getJobsList(params);
      setJobs(response.jobs);
      setTotalPages(response.pagination.pages);
      setTotalJobs(response.pagination.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  };

  const loadJobDetails = async (jobId: string) => {
    try {
      setDetailsLoading(true);
      const jobDetails = await api.getJobStatus(jobId);
      setSelectedJob(jobDetails);
      setDetailsOpen(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load job details");
    } finally {
      setDetailsLoading(false);
    }
  };

  const clearFilters = () => {
    setStatusFilter("");
    setTaskTypeFilter("");
    setSearchTerm("");
    setPage(1);
  };

  const handlePageChange = (
    event: React.ChangeEvent<unknown>,
    value: number
  ) => {
    setPage(value);
  };

  // Auto-refresh effect
  useEffect(() => {
    loadJobs();

    if (autoRefresh) {
      const interval = setInterval(loadJobs, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [page, statusFilter, taskTypeFilter, autoRefresh]);

  // Filter jobs by search term
  const filteredJobs = jobs.filter((job) => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      job.job_id.toLowerCase().includes(search) ||
      job.task_type.toLowerCase().includes(search) ||
      job.status.toLowerCase().includes(search)
    );
  });

  return (
    <Card sx={{ maxWidth: 1200, mx: "auto", mt: 4 }}>
      <CardContent>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 3,
          }}
        >
          <Typography variant="h5" gutterBottom>
            Job Dashboard
          </Typography>
          <Box>
            <Tooltip title="Toggle auto-refresh">
              <IconButton
                onClick={() => setAutoRefresh(!autoRefresh)}
                color={autoRefresh ? "primary" : "default"}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh now">
              <IconButton onClick={loadJobs} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Filters */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
            <FilterIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Filters</Typography>
          </Box>

          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="">All Statuses</MenuItem>
                  <MenuItem value="queued">Queued</MenuItem>
                  <MenuItem value="in_progress">In Progress</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Task Type</InputLabel>
                <Select
                  value={taskTypeFilter}
                  label="Task Type"
                  onChange={(e) => setTaskTypeFilter(e.target.value)}
                >
                  <MenuItem value="">All Types</MenuItem>
                  <MenuItem value="email_send">Send Email</MenuItem>
                  <MenuItem value="data_process">Process Data</MenuItem>
                  <MenuItem value="webhook_call">Webhook Call</MenuItem>
                  <MenuItem value="file_upload">File Upload</MenuItem>
                  <MenuItem value="report_generate">Generate Report</MenuItem>
                  <MenuItem value="custom_task">Custom Task</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                label="Search"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by ID, type, or status"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                startIcon={<ClearIcon />}
                onClick={clearFilters}
                fullWidth
              >
                Clear Filters
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {/* Jobs Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Job ID</TableCell>
                <TableCell>Task Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Retry Count</TableCell>
                <TableCell>Callback Retries</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : filteredJobs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary">
                      No jobs found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredJobs.map((job) => (
                  <TableRow key={job.job_id} hover>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {truncateId(job.job_id)}
                      </Typography>
                    </TableCell>
                    <TableCell>{job.task_type}</TableCell>
                    <TableCell>
                      <Chip
                        label={job.status}
                        color={getStatusColor(job.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{job.retry_count}</TableCell>
                    <TableCell>{job.callback_retry_count}</TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(job.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => loadJobDetails(job.job_id)}
                          disabled={detailsLoading}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        {totalPages > 1 && (
          <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={handlePageChange}
              color="primary"
            />
          </Box>
        )}

        {/* Summary */}
        <Box sx={{ mt: 2, textAlign: "center" }}>
          <Typography variant="body2" color="text.secondary">
            Showing {filteredJobs.length} of {totalJobs} jobs
            {autoRefresh && " (auto-refreshing every 5 seconds)"}
          </Typography>
        </Box>

        {/* Job Details Dialog */}
        <Dialog
          open={detailsOpen}
          onClose={() => setDetailsOpen(false)}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: {
              borderRadius: 2,
              boxShadow: "0 8px 32px rgba(0,0,0,0.12)",
            },
          }}
        >
          <DialogTitle
            sx={{
              borderBottom: "1px solid",
              borderColor: "divider",
              pb: 2,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <Box>
              <Typography variant="h6" component="div">
                Job Details
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Complete information about this job
              </Typography>
            </Box>
            <IconButton
              onClick={() => setDetailsOpen(false)}
              size="small"
              sx={{ color: "text.secondary" }}
            >
              <ClearIcon />
            </IconButton>
          </DialogTitle>

          <DialogContent sx={{ pt: 3 }}>
            {detailsLoading ? (
              <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
                <CircularProgress />
              </Box>
            ) : selectedJob ? (
              <Box>
                {/* Header Section */}
                <Box sx={{ mb: 4 }}>
                  <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                    <Typography variant="h6" sx={{ mr: 2 }}>
                      {selectedJob.task_type}
                    </Typography>
                    <Chip
                      label={selectedJob.status}
                      color={getStatusColor(selectedJob.status) as any}
                      size="small"
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>
                  <Typography
                    variant="body2"
                    fontFamily="monospace"
                    color="text.secondary"
                    sx={{ fontSize: "0.875rem" }}
                  >
                    {selectedJob.job_id}
                  </Typography>
                </Box>

                {/* Main Information Grid */}
                <Grid container spacing={3} sx={{ mb: 4 }}>
                  <Grid item xs={12} sm={6}>
                    <Box sx={{ p: 2, bgcolor: "grey.50", borderRadius: 1 }}>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        display="block"
                      >
                        Created At
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {formatDate(selectedJob.created_at)}
                      </Typography>
                    </Box>
                  </Grid>

                  {selectedJob.updated_at && (
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ p: 2, bgcolor: "grey.50", borderRadius: 1 }}>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          display="block"
                        >
                          Updated At
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {formatDate(selectedJob.updated_at)}
                        </Typography>
                      </Box>
                    </Grid>
                  )}

                  <Grid item xs={12} sm={6}>
                    <Box sx={{ p: 2, bgcolor: "grey.50", borderRadius: 1 }}>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        display="block"
                      >
                        Job Retry Count
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {selectedJob.retry_count}
                      </Typography>
                    </Box>
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <Box sx={{ p: 2, bgcolor: "grey.50", borderRadius: 1 }}>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        display="block"
                      >
                        Callback Retry Count
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {selectedJob.callback_retry_count}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {/* Callback URL Section */}
                {selectedJob.callback_url && (
                  <Box sx={{ mb: 4 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Callback URL
                    </Typography>
                    <Paper
                      sx={{
                        p: 2,
                        bgcolor: "primary.50",
                        border: "1px solid",
                        borderColor: "primary.200",
                        borderRadius: 1,
                      }}
                    >
                      <Typography
                        variant="body2"
                        fontFamily="monospace"
                        sx={{ wordBreak: "break-all", fontSize: "0.875rem" }}
                      >
                        {selectedJob.callback_url}
                      </Typography>
                    </Paper>
                  </Box>
                )}

                {/* Payload Section */}
                {selectedJob.payload && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Payload Data
                    </Typography>
                    <Paper
                      sx={{
                        p: 2,
                        bgcolor: "grey.50",
                        border: "1px solid",
                        borderColor: "divider",
                        borderRadius: 1,
                        maxHeight: 300,
                        overflow: "auto",
                      }}
                    >
                      <pre
                        style={{
                          margin: 0,
                          fontFamily: "monospace",
                          fontSize: "0.875rem",
                          lineHeight: 1.5,
                          color: "#374151",
                        }}
                      >
                        {JSON.stringify(selectedJob.payload, null, 2)}
                      </pre>
                    </Paper>
                  </Box>
                )}
              </Box>
            ) : null}
          </DialogContent>

          <DialogActions sx={{ p: 3, pt: 0 }}>
            <Button
              variant="outlined"
              onClick={() => setDetailsOpen(false)}
              startIcon={<ClearIcon />}
            >
              Close
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
}
