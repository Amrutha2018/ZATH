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

interface ForgotPasswordFormProps {
  onBackToLogin: () => void;
  onResetPassword: (email: string) => void;
}

export function ForgotPasswordForm({
  onBackToLogin,
  onResetPassword,
}: ForgotPasswordFormProps) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await api.forgotPassword(email);
      if (response.user_exists) {
        setSuccess(true);
      } else {
        setError("No account found with this email address.");
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          "Failed to process request. Please try again."
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
            Account Found
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            align="center"
            sx={{ mb: 3 }}
          >
            We found an account for <strong>{email}</strong>
          </Typography>
          <Alert severity="success" sx={{ mb: 2 }}>
            Account verified successfully!
          </Alert>
          <Typography
            variant="body2"
            color="text.secondary"
            align="center"
            sx={{ mb: 2 }}
          >
            You can now set a new password for your account.
          </Typography>
          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={() => onResetPassword(email)}
            sx={{ mb: 2 }}
          >
            Set New Password
          </Button>
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
          Forgot Password
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          align="center"
          sx={{ mb: 3 }}
        >
          Enter your email address to verify your account and reset your
          password
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            sx={{ mb: 3 }}
            disabled={loading}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={loading || !email}
            sx={{ mb: 2 }}
          >
            {loading ? "Verifying..." : "Verify Account"}
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
