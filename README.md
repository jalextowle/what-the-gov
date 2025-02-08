# What the Gov

An AI-powered platform for understanding U.S. Executive Orders and government actions. Ask questions in plain English and get insights about executive orders, their impacts, and the changing landscape of presidential power.

## Features

- **Executive Order Analysis**: Track and analyze executive orders in real-time
- **Natural Language Interface**: Ask questions about executive orders in plain English
- **Smart Summaries**: Get concise summaries of executive order impacts and themes
- **Historical Context**: Understand how current orders relate to past presidential actions
- **Modern UI**: Clean, responsive interface with dark mode support

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- Federal Register API
- OpenAI API
- LangChain

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- React Markdown

## Getting Started

### Prerequisites
- Python 3.11 (Required for FAISS compatibility)
- Node.js 18+
- OpenAI API key
- SWIG (Required for building FAISS)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/what-the-gov.git
   cd what-the-gov
   ```

2. Set up the backend:
   ```bash
   cd backend
   python3.11 -m venv venv  # Must use Python 3.11 for FAISS compatibility
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   ```

4. Create a .env file in the backend directory:
   ```
   OPENAI_API_KEY=your_api_key_here
   ENVIRONMENT=development
   ALLOWED_HOSTS=localhost,127.0.0.1
   ALLOWED_ORIGINS=http://localhost:3000
   RATE_LIMIT=20/minute
   ```

### Running the Application

1. Start the backend server (this command will also handle restarting):
   ```bash
   lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null; cd backend && source venv/bin/activate && uvicorn main:app --reload
   ```

2. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open http://localhost:3000 in your browser

### Environment Variables

- **ENVIRONMENT**: Set to `development` or `production`
- **ALLOWED_HOSTS**: Comma-separated list of allowed hosts (e.g., `localhost,127.0.0.1`)
- **ALLOWED_ORIGINS**: Comma-separated list of allowed CORS origins (e.g., `http://localhost:3000`)
- **RATE_LIMIT**: API rate limit (default: `20/minute`)
- **OPENAI_API_KEY**: Your OpenAI API key

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
