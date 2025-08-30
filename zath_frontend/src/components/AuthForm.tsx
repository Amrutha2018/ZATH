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
  Chip,
  Link,
} from "@mui/material";
import { api } from "@/lib/api";

interface AuthFormProps {
  onSwitchToLogin?: () => void;
}

export function AuthForm({ onSwitchToLogin }: AuthFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [apiKey, setApiKey] = useState("");

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const user = await api.register(email, password);
      setApiKey(user.api_key);
      setSuccess("Registration successful! Your API key has been generated.");

      // Store API key in localStorage
      localStorage.setItem("zath_api_key", user.api_key);

      // Trigger page refresh to update auth state
      window.location.reload();
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card sx={{ maxWidth: 500, mx: "auto", mt: 4 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Register for ZATH
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Create an account with email and password to get an API key for
          accessing ZATH services.
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

        <Box component="form" onSubmit={handleRegister}>
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
            helperText="Minimum 6 characters"
          />

          <Button
            type="submit"
            variant="contained"
            fullWidth
            disabled={loading || !email || !password}
            sx={{ mb: 2 }}
          >
            {loading ? "Registering..." : "Register"}
          </Button>
        </Box>

        {apiKey && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Your API Key:
            </Typography>
            <Chip
              label={apiKey}
              variant="outlined"
              sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}
            />
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              This key has been saved automatically and will be used for API
              requests.
            </Typography>
          </Box>
        )}

        {onSwitchToLogin && (
          <Box sx={{ textAlign: "center", mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Already have an account?{" "}
              <Link
                component="button"
                variant="body2"
                onClick={onSwitchToLogin}
                sx={{ cursor: "pointer" }}
              >
                Login here
              </Link>
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
