# PolicyPal

PolicyPal is an AI-powered chat interface for understanding U.S. Executive Orders. It allows users to ask questions about Executive Orders and receive answers with specific citations to source documents.

## Project Structure

```
policypal/
├── backend/              # FastAPI backend
│   ├── main.py          # Main FastAPI application
│   ├── models.py        # SQLAlchemy database models
│   ├── processor.py     # Document processing and embedding
│   ├── scraper.py       # Executive Order scraper
│   └── requirements.txt # Python dependencies
└── frontend/            # Next.js frontend (to be set up)
```

## Setup Instructions

### Backend Setup

1. Create a virtual environment and activate it:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```

4. Start the backend server:
```bash
uvicorn main:app --reload
```

### Frontend Setup

The frontend setup will use Next.js 14 with:
- TypeScript for type safety
- Tailwind CSS for styling
- shadcn/ui for UI components

(Frontend setup instructions will be added after creating the Next.js project)

## Features

- Scrapes and stores Executive Orders from whitehouse.gov (2024)
- Processes documents into chunks for efficient AI context
- Provides a mobile-responsive chat interface
- Returns answers with specific citations to source documents
- Uses OpenAI's GPT models for accurate and contextual responses

## Architecture

- Frontend: Next.js, Tailwind CSS, shadcn/ui components
- Backend: Python FastAPI
- Database: SQLite
- AI: OpenAI API, LangChain
- Hosting: Vercel (frontend), Railway (backend)
