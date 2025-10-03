"use client";

import { useState, useEffect } from "react";
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
  Button,
  Alert,
  Paper,
} from "@mui/material";
import { AuthForm } from "./AuthForm";
import { LoginForm } from "./LoginForm";
import { ForgotPasswordForm } from "./ForgotPasswordForm";
import { SimpleResetPasswordForm } from "./SimpleResetPasswordForm";
import { JobForm } from "./JobForm";
import { JobDashboard } from "./JobDashboard";
import { api } from "@/lib/api";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

type AuthMode =
  | "login"
  | "register"
  | "forgot-password"
  | "simple-reset-password";

export function Dashboard() {
  const [tabValue, setTabValue] = useState(0);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [connectionStatus, setConnectionStatus] = useState<
    "checking" | "connected" | "error"
  >("checking");
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [resetEmail, setResetEmail] = useState("");

  useEffect(() => {
    // Check if user is authenticated
    const storedApiKey = localStorage.getItem("zath_api_key");
    if (storedApiKey) {
      setApiKey(storedApiKey);
      setIsAuthenticated(true);
      checkConnection();
    } else {
      setConnectionStatus("error");
    }
  }, []);

  const checkConnection = async () => {
    try {
      await api.healthCheck();
      setConnectionStatus("connected");
    } catch (error) {
      setConnectionStatus("error");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("zath_api_key");
    localStorage.removeItem("zath_token");
    setIsAuthenticated(false);
    setApiKey("");
    setConnectionStatus("error");
  };

  const handleAuthSuccess = (user: { api_key: string }) => {
    setIsAuthenticated(true);
    setApiKey(user.api_key);
    checkConnection();
  };

  const switchToRegister = () => {
    setAuthMode("register");
  };

  const switchToLogin = () => {
    setAuthMode("login");
  };

  const switchToForgotPassword = () => {
    setAuthMode("forgot-password");
  };

  const switchToSimpleResetPassword = (email: string) => {
    setResetEmail(email);
    setAuthMode("simple-reset-password");
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (!isAuthenticated) {
    return (
      <Container maxWidth="md">
        <Box sx={{ textAlign: "center", py: 4 }}>
          <Typography variant="h3" gutterBottom>
            ZATH Dashboard
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
            Asynchronous Job Processing System
          </Typography>
          {authMode === "login" ? (
            <LoginForm
              onLoginSuccess={handleAuthSuccess}
              onSwitchToRegister={switchToRegister}
              onForgotPassword={switchToForgotPassword}
            />
          ) : authMode === "register" ? (
            <AuthForm onSwitchToLogin={switchToLogin} />
          ) : authMode === "forgot-password" ? (
            <ForgotPasswordForm
              onBackToLogin={switchToLogin}
              onResetPassword={switchToSimpleResetPassword}
            />
          ) : (
            <SimpleResetPasswordForm
              email={resetEmail}
              onBackToLogin={switchToLogin}
            />
          )}
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 4,
          }}
        >
          <Box>
            <Typography variant="h3" gutterBottom>
              ZATH Dashboard
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Asynchronous Job Processing System
            </Typography>
          </Box>

          <Box sx={{ textAlign: "right" }}>
            <Button variant="outlined" onClick={handleLogout} sx={{ mb: 1 }}>
              Logout
            </Button>
            <Box>
              <Typography variant="caption" color="text.secondary">
                API Key: {apiKey.substring(0, 8)}...
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Connection Status */}
        {connectionStatus === "checking" && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Checking connection to ZATH API...
          </Alert>
        )}

        {connectionStatus === "connected" && (
          <Alert severity="success" sx={{ mb: 3 }}>
            Connected to ZATH API successfully
          </Alert>
        )}

        {connectionStatus === "error" && (
          <Alert severity="error" sx={{ mb: 3 }}>
            Cannot connect to ZATH API. Please ensure the backend is running on
            http://localhost:8000
          </Alert>
        )}

        {/* Tabs */}
        <Paper sx={{ width: "100%" }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="ZATH Dashboard tabs"
          >
            <Tab label="Create Job" />
            <Tab label="Job Dashboard" />
          </Tabs>
        </Paper>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <JobForm />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <JobDashboard />
        </TabPanel>
      </Box>
    </Container>
  );
}
