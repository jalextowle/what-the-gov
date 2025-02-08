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
- Python 3.10+
- Node.js 18+
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/what-the-gov.git
   cd what-the-gov
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
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
   ```

### Running the Application

1. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open http://localhost:3000 in your browser

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
