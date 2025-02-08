import aiohttp
import asyncio
import json
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import re
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple
from urllib.parse import urlencode
from models import ExecutiveOrder, DocumentChunk

# Configure logging to show debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EOScraper:
    BASE_URL = "https://www.federalregister.gov/api/v1/documents"
    
    async def fetch_page(self, url: str) -> str:
        """Fetch a page from a URL."""
        logger.info(f"Fetching URL: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching {url}: Status {response.status}")
                        logger.error(f"Response: {await response.text()}")
                        return None
                    return await response.text()
        except Exception as e:
            logger.error(f"Exception fetching {url}: {str(e)}")
            return None

    def build_api_url(self, year: int) -> str:
        """Build the API URL for fetching Executive Orders."""
        params = [
            ('conditions[type][]', 'PRESDOCU'),
            ('conditions[presidential_document_type][]', 'executive_order'),
            ('conditions[correction]', '0'),
            ('fields[]', 'executive_order_number'),
            ('fields[]', 'title'),
            ('fields[]', 'raw_text_url'),
            ('fields[]', 'html_url'),
            ('fields[]', 'signing_date'),
            ('fields[]', 'publication_date'),
            ('fields[]', 'president'),
            ('fields[]', 'executive_order_notes'),
            ('fields[]', 'disposition_notes'),
            ('per_page', '100'),
            ('order', 'executive_order_number'),
            ('conditions[publication_date][year]', str(year))
        ]
        
        query_string = urlencode(params, doseq=True)
        url = f"{self.BASE_URL}?{query_string}"
        logger.debug(f"Built API URL: {url}")
        return url

    async def fetch_eo_text(self, raw_text_url: str) -> str:
        """Fetch the full text of an Executive Order from its raw text URL."""
        logger.info(f"Fetching EO text from: {raw_text_url}")
        content = await self.fetch_page(raw_text_url)
        if not content:
            return ""
        return content

    async def parse_eo_response(self, json_content: str) -> List[Dict]:
        """Parse the response from the Federal Register API."""
        try:
            data = json.loads(json_content)
            eo_items = []
            
            for result in data.get('results', []):
                # Extract the EO number from the executive_order_number field
                eo_number = result.get('executive_order_number')
                if not eo_number:
                    logger.warning(f"No executive order number found for document: {result.get('document_number')}")
                    continue
                
                # Parse the signing date
                try:
                    date = datetime.strptime(result.get('signing_date', ''), '%Y-%m-%d')
                except ValueError as e:
                    logger.error(f"Failed to parse signing date for EO {eo_number}: {e}")
                    continue
                
                # Fetch the full text
                raw_text_url = result.get('raw_text_url')
                if not raw_text_url:
                    logger.warning(f"No raw text URL found for EO {eo_number}")
                    continue
                
                full_text = await self.fetch_eo_text(raw_text_url)
                if not full_text:
                    logger.error(f"Failed to fetch full text for EO {eo_number}")
                    continue
                
                # Determine president and administration using the API's president data
                president, administration = self.determine_president_and_administration(result.get('president'))
                
                eo_data = {
                    'title': result.get('title', ''),
                    'url': result.get('html_url', ''),
                    'date': date,
                    'order_number': str(eo_number),
                    'full_text': full_text,
                    'president': president,
                    'administration': administration
                }
                
                logger.info(f"Found EO {eo_data['order_number']} - {eo_data['title']} (Signed: {eo_data['date']}, President: {president})")
                eo_items.append(eo_data)
            
            logger.info(f"Found {len(eo_items)} Executive Orders")
            return eo_items
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []

    def determine_president_and_administration(self, president_data: dict) -> Tuple[str, str]:
        """Determine the president and administration based on the API's president data."""
        if not president_data:
            return "Unknown", "Unknown Administration"
            
        president_name = president_data.get('name', '')
        if 'Biden' in president_name:
            return "Joseph R. Biden", "Biden Administration (2021-2025)"
        elif 'Trump' in president_name:
            return "Donald J. Trump", "Trump Administration (2025-)"
        else:
            return president_name, f"{president_name.split()[-1]} Administration"

    async def scrape_executive_orders(self, db: Session, year: int = 2024) -> List[ExecutiveOrder]:
        logger.info(f"Starting to scrape Executive Orders for year {year}")
        
        # Build the API URL
        api_url = self.build_api_url(year)
        logger.info(f"Built API URL: {api_url}")
        
        # Fetch the data from the Federal Register API
        json_content = await self.fetch_page(api_url)
        if not json_content:
            logger.error("Failed to fetch data from Federal Register API")
            return []
        
        logger.info("Successfully fetched data from Federal Register API")
        logger.info(f"Response preview: {json_content[:500]}")
            
        eo_items = await self.parse_eo_response(json_content)
        logger.info(f"Parsed {len(eo_items)} executive orders from response")
        
        # Process each EO and add to database
        eos = []
        for eo_info in eo_items:
            # Check if EO already exists
            existing_eo = db.query(ExecutiveOrder).filter_by(
                order_number=eo_info['order_number']
            ).first()
            
            if existing_eo:
                logger.info(f"EO {eo_info['order_number']} already exists in database")
                continue
            
            # Create new EO
            eo = ExecutiveOrder(
                order_number=eo_info['order_number'],
                title=eo_info['title'],
                date_signed=eo_info['date'],
                president=eo_info['president'],
                administration=eo_info['administration'],
                url=eo_info['url'],
                full_text=eo_info['full_text']
            )
            
            try:
                db.add(eo)
                db.commit()
                eos.append(eo)
                logger.info(f"Successfully added EO {eo_info['order_number']} to database")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to add EO {eo_info['order_number']} to database: {str(e)}")
        
        logger.info(f"Finished processing {len(eos)} new executive orders")
        return eos
