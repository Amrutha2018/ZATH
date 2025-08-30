# ZATH Frontend

A modern Next.js frontend for the ZATH Asynchronous Job Processing System.

## 🚀 Features

- **Authentication System**: Email/password registration and login with JWT tokens
- **Password Reset**: Simple password reset flow without email service dependency
- **Job Management**: Create and monitor asynchronous jobs
- **Real-time Updates**: Live job status updates and dashboard
- **Responsive Design**: Material-UI based modern interface
- **TypeScript**: Full type safety throughout the application

## 🛠️ Tech Stack

- **Framework**: Next.js 15.5.2
- **UI Library**: Material-UI (MUI) v7
- **HTTP Client**: Axios
- **Language**: TypeScript
- **Styling**: Emotion (CSS-in-JS)

## 📁 Project Structure

```
src/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout with theme provider
│   ├── page.tsx           # Main page component
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── Dashboard.tsx      # Main dashboard with tabs
│   ├── AuthForm.tsx       # User registration form
│   ├── LoginForm.tsx      # User login form
│   ├── ForgotPasswordForm.tsx    # Password reset request
│   ├── SimpleResetPasswordForm.tsx  # Direct password reset
│   ├── JobForm.tsx        # Job creation form
│   ├── JobDashboard.tsx   # Job listing and management
│   └── ThemeProvider.tsx  # MUI theme configuration
└── lib/
    └── api.ts             # API client and type definitions
```

## 🔧 Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

### Build for Production

```bash
npm run build
npm start
```

## 🔌 API Integration

The frontend communicates with the ZATH backend API running on `http://localhost:8000`. The API client is configured in `src/lib/api.ts` with:

- Automatic API key/JWT token injection
- Error handling and authentication state management
- TypeScript interfaces for all API responses

## 🎨 UI Components

### Authentication Flow

1. **Login**: Email/password authentication with JWT tokens
2. **Registration**: New user account creation
3. **Password Reset**: Simple flow without email service
   - Enter email to verify account
   - Set new password directly
   - Return to login

### Job Management

1. **Create Job**: Form to submit new asynchronous jobs
2. **Job Dashboard**: List, filter, and monitor job status
3. **Real-time Updates**: Automatic status refresh

## 🔒 Security Features

- JWT token-based authentication
- API key management for programmatic access
- Secure password handling
- CORS configuration for local development

## 🐳 Docker Support

The frontend is containerized and can be run with Docker Compose:

```bash
docker compose up zathfrontend
```

## 📝 Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)

## 🧪 Testing

The frontend is designed to work seamlessly with the ZATH backend. All features have been tested with the complete authentication and job processing flow.
