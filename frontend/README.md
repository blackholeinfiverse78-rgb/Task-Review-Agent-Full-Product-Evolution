# React Frontend for Parikshak

This is a modern React-based frontend for the Parikshak system.

## Local Development

1. **Install dependencies**:
   ```bash
   cd frontend-react
   npm install
   ```

2. **Set backend URL** (optional):
   Create a `.env` file in the `frontend-react` directory:
   ```
   REACT_APP_BACKEND_URL=http://localhost:8000/api/v1/task
   ```

3. **Start development server**:
   ```bash
   npm start
   ```
   The app will open at `http://localhost:3000`

## Production Build

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Features

- ✨ Modern, responsive UI with smooth animations
- 🎨 Beautiful gradient design with glassmorphism effects
- 🚀 Real-time backend status indicator
- 📊 Interactive progress bars and metrics
- 🎯 Pre-loaded demo scenarios
- 💡 Comprehensive error handling
- 📱 Mobile-friendly responsive design

## Environment Variables

- `REACT_APP_BACKEND_URL`: Backend API URL (default: `http://localhost:8000/api/v1/task`)
