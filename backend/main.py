import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBasic
from sqlalchemy.orm import Session
from typing import List, Optional
from dotenv import load_dotenv
from models import ExecutiveOrder
from database import get_db, init_db
from processor import DocumentProcessor
from scraper import EOScraper
from pydantic import BaseModel
from langchain_openai import OpenAI, OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores.faiss import FAISS
import logging
import json
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

# Add trusted host middleware in production
if ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=ALLOWED_HOSTS
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

engine = init_db()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Rate limit configuration
RATE_LIMIT = os.getenv("RATE_LIMIT", "20/minute")  # Default: 20 requests per minute

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Dependency to get database session
def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    message: str
    chat_history: List[dict] = []

logger = logging.getLogger(__name__)

def generate_eo_summary(db: Session) -> str:
    """Generate a summary of executive orders by administration and year."""
    
    # Get all executive orders ordered by date
    eos = db.query(ExecutiveOrder).order_by(ExecutiveOrder.date_signed).all()
    
    # Group by administration and year
    admin_summary = {}
    for eo in eos:
        year = eo.date_signed.year
        admin = eo.administration
        if admin not in admin_summary:
            admin_summary[admin] = {"total": 0, "years": {}}
        if year not in admin_summary[admin]["years"]:
            admin_summary[admin]["years"][year] = []
        admin_summary[admin]["years"][year].append(eo)
        admin_summary[admin]["total"] += 1
    
    # Build summary text
    summary = []
    for admin, data in admin_summary.items():
        admin_lines = [f"\n{admin}:"]
        admin_lines.append(f"Total Executive Orders: {data['total']}")
        
        for year, eos in sorted(data["years"].items()):
            year_eos = [f"EO {eo.order_number}: {eo.title}" for eo in eos]
            admin_lines.append(f"\n{year} ({len(eos)} orders):")
            admin_lines.extend([f"- {eo}" for eo in year_eos])
        
        summary.extend(admin_lines)
    
    return "\n".join(summary)

@app.post("/api/ingest")
@limiter.limit(RATE_LIMIT)
async def ingest_documents(request: Request, db: Session = Depends(get_db)):
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    scraper = EOScraper()
    processor = DocumentProcessor(openai_api_key)
    
    # Scrape executive orders from both 2024 and 2025
    total_eos = []
    for year in [2024, 2025]:
        try:
            logger.info(f"Starting to scrape executive orders for {year}")
            eos = await scraper.scrape_executive_orders(db, year=year)
            if eos:
                total_eos.extend(eos)
                logger.info(f"Successfully scraped {len(eos)} executive orders for {year}")
            else:
                logger.error(f"No executive orders found for {year}")
        except Exception as e:
            logger.error(f"Error scraping executive orders for {year}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error scraping executive orders for {year}: {str(e)}")
    
    if not total_eos:
        raise HTTPException(status_code=500, detail="No executive orders were found")
    
    # Process documents
    try:
        await processor.process_all_documents(db)
        logger.info("Successfully processed all documents")
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")
    
    return {"message": f"Processed {len(total_eos)} new executive orders"}

@app.post("/api/chat")
@limiter.limit(RATE_LIMIT)
async def chat(request: Request, chat_request: ChatRequest, db: Session = Depends(get_db)):
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    # Format chat history
    formatted_history = ""
    if chat_request.chat_history:
        for msg in chat_request.chat_history:
            if msg.get('human') and msg.get('ai'):
                formatted_history += f"Human: {msg['human']}\nAssistant: {msg['ai']}\n\n"

    # Generate EO summary
    eo_summary = generate_eo_summary(db)

    # Initialize OpenAI
    llm = ChatOpenAI(
        api_key=openai_api_key,
        model="gpt-4-turbo-preview",
        temperature=0
    )

    embeddings = OpenAIEmbeddings(
        api_key=openai_api_key
    )

    # Create vector store
    vectorstore = FAISS.from_texts(
        [chunk.content for eo in db.query(ExecutiveOrder).all() for chunk in eo.chunks],
        embeddings
    )
    
    # Get relevant documents
    docs = vectorstore.similarity_search(chat_request.message, k=3)
    context = "\n\n".join(doc.page_content for doc in docs)
    
    # Create prompt
    prompt = f"""You are an AI assistant that helps users understand executive orders and government actions. 
Your responses should be clear, accurate, and based on the provided context from executive orders.

Executive Order Summary:
{eo_summary}

Current conversation:
{formatted_history}

Question: {chat_request.message}

Additional context from the executive orders:
{context}

Please provide a clear and informative response based on the executive orders and context provided. If you cannot find relevant information in the context, say so."""

    # Get response from OpenAI
    response = llm.invoke(prompt)
    
    return {"response": response.content, "sources": []}
