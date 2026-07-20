# FuelSense — Vercel Deployment Guide

This guide outlines the step-by-step process of deploying the FuelSense FastAPI backend and React frontend to Vercel (free serverless tier) and configuring the environment variables.

---

## 🐍 Backend Deployment (Python FastAPI)

The backend is configured for Vercel Serverless Functions using the `@vercel/python` runtime. It dynamically replicates the SQLite database structure to the writable `/tmp` folder on execution, making it fully serverless-compliant.

### 1. Requirements & Configuration Files
We have created the following files inside the `backend/` directory:
- [index.py](file:///c:/Users/User/Documents/trae_projects/FuelSenseSim/backend/api/index.py): Vercel entrypoint. Dynamically maps paths so package imports work seamlessly.
- [requirements.txt](file:///c:/Users/User/Documents/trae_projects/FuelSenseSim/backend/requirements.txt): List of Python dependencies.
- [vercel.json](file:///c:/Users/User/Documents/trae_projects/FuelSenseSim/backend/vercel.json): Vercel configuration specifying routing and runtime rules.

### 2. Deploying via Vercel Dashboard
1. Go to the [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New** > **Project**.
2. Import the Git repository containing `FuelSenseSim`.
3. In the project setup panel:
   - **Framework Preset**: Other (Vercel automatically detects Python)
   - **Root Directory**: Select `backend` (Ensure this is set to the `backend` subfolder)
4. Click **Environment Variables** and add:
   - `DEEPSEEK_API_KEY`: Your DeepSeek API key (optional).
   - `DEEPSEEK_BASE_URL`: `https://api.deepseek.com` (optional).
   - `FUEL_SENSE_DEMO_MODE`: Set to `true` if you want to bypass the DeepSeek client and run on pre-defined local fallback templates (recommended for showcasing without rate limit or cost worries).
5. Click **Deploy**. Vercel will build the serverless function and output a deployment URL (e.g., `https://fuelsense-backend.vercel.app`).

### 3. Deploying via Vercel CLI
If you prefer terminal deployment, run the following commands:
```bash
# Install Vercel CLI if you haven't already
npm install -g vercel

# Navigate to backend directory
cd backend

# Deploy to Vercel
vercel
```
Follow the interactive CLI prompts to link the project and deploy. Use `vercel --prod` to release to production.

---

## ⚛️ Frontend Deployment (React + Vite)

The frontend is deployed as a static application on Vercel.

### 1. Deploying via Vercel Dashboard
1. In the Vercel Dashboard, click **Add New** > **Project** and import the same repository.
2. In the project setup panel:
   - **Framework Preset**: Vite
   - **Root Directory**: Select `frontend` (Ensure this is set to the `frontend` subfolder)
   - **Build Command**: `npm run build` or `vite build`
   - **Output Directory**: `dist`
3. Click **Environment Variables** and add:
   - `VITE_API_BASE_URL`: The URL of your deployed backend (e.g., `https://fuelsense-backend.vercel.app`, with no trailing slash).
4. Click **Deploy**. Vercel will build and serve your frontend static assets.

---

## 💻 Local Testing & Verification

### Running the Backend Locally
1. Start the FastAPI backend:
   ```bash
   uvicorn backend.main:app --reload
   ```
2. The API will be available at `http://127.0.0.1:8000`. You can inspect the docs at `http://127.0.0.1:8000/docs`.

### Running the Frontend Locally
1. Create a `frontend/.env` file with:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```
2. Run Vite local server:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser.

### Verifying catch-up simulation
* In a serverless state, the simulation updates based on elapsed time when you poll. You do not need to run backend threads. The state remains 100% deterministic and synchronized with the frontend.
