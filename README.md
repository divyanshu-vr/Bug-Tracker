# BugTrackr

A lightweight, developer-friendly bug tracking application built with FastAPI and Next.js.

## Project Structure

```
bugtrackr-app/
├── backend/
│   ├── main.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── pages/
│   ├── components/
│   ├── utils/
│   ├── styles/
│   ├── package.json
│   └── .env.local.example
└── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and configure your environment variables

5. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Copy `.env.local.example` to `.env.local` and configure your environment variables

4. Run the development server:
   ```bash
   npm run dev
   ```

## Technology Stack

- **Backend**: FastAPI, Python 3.11+, MongoDB Atlas, Cloudinary
- **Frontend**: Next.js 14, TypeScript, TailwindCSS, Axios
- **External Services**: AppFlyte API, MongoDB Atlas, Cloudinary
