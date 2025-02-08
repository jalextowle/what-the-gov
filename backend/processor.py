import json
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session
from models import ExecutiveOrder, DocumentChunk

class DocumentProcessor:
    def __init__(self, openai_api_key: str):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    
    async def process_document(self, db: Session, executive_order: ExecutiveOrder):
        # Split the document into chunks
        chunks = self.text_splitter.split_text(executive_order.full_text)
        
        # Create embeddings for each chunk
        embeddings = await self.embeddings.aembed_documents(chunks)
        
        # Store chunks and embeddings
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc_chunk = DocumentChunk(
                executive_order_id=executive_order.id,
                content=chunk,
                chunk_index=i,
                embedding=json.dumps(embedding)
            )
            db.add(doc_chunk)
        
        db.commit()
    
    async def process_all_documents(self, db: Session):
        unprocessed_docs = db.query(ExecutiveOrder)\
            .filter(~ExecutiveOrder.chunks.any())\
            .all()
        
        for doc in unprocessed_docs:
            await self.process_document(db, doc)
