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

interface LoginFormProps {
  onLoginSuccess: (user: any) => void;
  onSwitchToRegister: () => void;
  onForgotPassword: () => void;
}

export function LoginForm({
  onLoginSuccess,
  onSwitchToRegister,
  onForgotPassword,
}: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // Login with email and password
      const tokenResponse = await api.login(email, password);

      // Store JWT token
      localStorage.setItem("zath_token", tokenResponse.access_token);

      // Get user info
      const user = await api.getCurrentUser();

      // Store API key for programmatic access
      localStorage.setItem("zath_api_key", user.api_key);

      onLoginSuccess(user);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          "Login failed. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card sx={{ maxWidth: 400, mx: "auto", mt: 4 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom align="center">
          Login to ZATH
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          align="center"
          sx={{ mb: 3 }}
        >
          Enter your email and password to access your dashboard
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
            sx={{ mb: 2 }}
            disabled={loading}
          />

          <TextField
            fullWidth
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            sx={{ mb: 2 }}
            disabled={loading}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={loading}
            sx={{ mb: 2 }}
          >
            {loading ? "Logging in..." : "Login"}
          </Button>

          <Box sx={{ textAlign: "right", mb: 2 }}>
            <Link
              component="button"
              variant="body2"
              onClick={(e) => {
                e.preventDefault();
                onForgotPassword();
              }}
              sx={{ cursor: "pointer", fontSize: "0.875rem" }}
            >
              Forgot Password?
            </Link>
          </Box>

          <Box sx={{ textAlign: "center" }}>
            <Typography variant="body2" color="text.secondary">
              Don't have an account?{" "}
              <Link
                component="button"
                variant="body2"
                onClick={(e) => {
                  e.preventDefault();
                  onSwitchToRegister();
                }}
                sx={{ cursor: "pointer" }}
              >
                Register here
              </Link>
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
