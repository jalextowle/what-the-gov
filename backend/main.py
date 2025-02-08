import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from models import init_db, ExecutiveOrder
from database import get_db
from scraper import EOScraper
from processor import DocumentProcessor
from pydantic import BaseModel
from typing import List, Tuple
import json
from langchain_openai import OpenAI, OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores.faiss import FAISS
import logging

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

engine = init_db()
openai_api_key = os.getenv("OPENAI_API_KEY")

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
async def ingest_documents(db: Session = Depends(get_db)):
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
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    # Format chat history
    formatted_history = ""
    if request.chat_history:
        for msg in request.chat_history:
            formatted_history += f"Human: {msg['human']}\nAssistant: {msg['ai']}\n\n"
    
    # Generate EO summary
    eo_summary = generate_eo_summary(db)
    
    # Get all document chunks and their embeddings
    chunks = []
    embeddings_list = []
    
    eos = db.query(ExecutiveOrder).all()
    if not eos:
        return {
            "answer": "No Executive Orders have been ingested yet. Please run the /api/ingest endpoint first."
        }
    
    for eo in eos:
        for chunk in eo.chunks:
            chunks.append(f"{chunk.content}\n\nSource: Executive Order {eo.order_number}")
            embeddings_list.append(json.loads(chunk.embedding))
    
    if not chunks:
        return {
            "answer": "No chunks found in the database. Please run the /api/ingest endpoint to process the documents."
        }
    
    # Create FAISS index
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = FAISS.from_embeddings(
        text_embeddings=list(zip(chunks, embeddings_list)),
        embedding=embeddings
    )
    
    # Create LLM
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=openai_api_key,
        model="gpt-4-turbo-preview"
    )
    
    # Get relevant documents
    docs = vectorstore.similarity_search(request.message, k=3)
    context = "\n\n".join(doc.page_content for doc in docs)
    
    # Create prompt
    prompt = f"""You are an AI assistant helping users understand Executive Orders. You have access to a database of real Executive Orders sourced directly from the Federal Register. Here is a summary of all available Executive Orders:

{eo_summary}

Important notes:
1. The above data comes directly from the Federal Register, which is the official source for U.S. Executive Orders
2. Donald J. Trump became president on January 20, 2025, succeeding Joseph R. Biden
3. For questions about Executive Orders from other time periods, I will inform you about this limitation

When answering questions:
1. Use the above summary to answer questions about counts, dates, and titles
2. Be specific about which administration issued each order
3. If asked about an executive order not in our database, clearly state that it's not in our current dataset
4. If relevant, mention when orders were signed relative to key events or other orders
5. DO NOT include any source citations or references in your response

Current conversation:
{formatted_history}

Question: {request.message}

Additional context from the executive orders:
{context}

Answer: """

    # Log the prompt for debugging
    logger.info("Generated prompt:")
    logger.info(prompt)
    
    # Get response from LLM
    response = await llm.ainvoke(prompt)
    
    async def format_theme(theme: str, description: str) -> str:
        return f"**{theme}**: {description}"

    async def format_themes(themes: List[Tuple[str, str]]) -> str:
        formatted_themes = []
        for theme, desc in themes:
            formatted_themes.append(f"1. **{theme}**: {desc}")
        return "\n\n".join(formatted_themes)
    
    return {
        "answer": response.content
    }
