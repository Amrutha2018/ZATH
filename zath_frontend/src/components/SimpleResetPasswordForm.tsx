"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  Box,
  Link,
} from "@mui/material";
import { api } from "@/lib/api";

interface SimpleResetPasswordFormProps {
  email: string;
  onBackToLogin: () => void;
}

export function SimpleResetPasswordForm({
  email,
  onBackToLogin,
}: SimpleResetPasswordFormProps) {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await api.simpleResetPassword(email, password);
      setSuccess(true);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          "Failed to reset password. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Card sx={{ maxWidth: 400, mx: "auto", mt: 4 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom align="center">
            Password Reset Successfully
          </Typography>
          <Alert severity="success" sx={{ mb: 2 }}>
            Your password has been reset successfully!
          </Alert>
          <Typography
            variant="body2"
            color="text.secondary"
            align="center"
            sx={{ mb: 2 }}
          >
            You can now log in with your new password.
          </Typography>
          <Box sx={{ textAlign: "center" }}>
            <Link
              component="button"
              variant="body2"
              onClick={onBackToLogin}
              sx={{ cursor: "pointer" }}
            >
              Back to Login
            </Link>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ maxWidth: 400, mx: "auto", mt: 4 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom align="center">
          Set New Password
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          align="center"
          sx={{ mb: 3 }}
        >
          Setting new password for <strong>{email}</strong>
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="New Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            sx={{ mb: 2 }}
            disabled={loading}
            helperText="Minimum 6 characters"
          />

          <TextField
            fullWidth
            label="Confirm New Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            sx={{ mb: 3 }}
            disabled={loading}
            error={confirmPassword !== "" && password !== confirmPassword}
            helperText={
              confirmPassword !== "" && password !== confirmPassword
                ? "Passwords do not match"
                : ""
            }
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={
              loading ||
              !password ||
              !confirmPassword ||
              password !== confirmPassword
            }
            sx={{ mb: 2 }}
          >
            {loading ? "Resetting..." : "Reset Password"}
          </Button>

          <Box sx={{ textAlign: "center" }}>
            <Typography variant="body2" color="text.secondary">
              Remember your password?{" "}
              <Link
                component="button"
                variant="body2"
                onClick={onBackToLogin}
                sx={{ cursor: "pointer" }}
              >
                Back to Login
              </Link>
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
