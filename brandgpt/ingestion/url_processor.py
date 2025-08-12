from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangchainDocument
from brandgpt.config import settings
import logging
from urllib.parse import urlparse, urljoin, urldefrag
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)


class URLScraper:
    def __init__(self, max_depth=1, max_links_per_page=20):
        self.max_depth = max_depth
        self.max_links_per_page = max_links_per_page
        self.visited_urls = set()
        self.content = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (BrandGPT Bot) AppleWebKit/537.36 (KHTML, like Gecko)'
        })
    
    def _extract_text(self, soup, url, depth):
        """Extract meaningful text content from the page"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ''
        
        # Extract main content (prioritize content areas)
        content_selectors = [
            'main', 'article', '.content', '#content', '.main-content',
            '.entry-content', '.post-content', '#main'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # Fallback to body if no main content area found
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Extract text from paragraphs, headings, and lists
        text_elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
        texts = [elem.get_text().strip() for elem in text_elements if elem.get_text().strip()]
        
        combined_text = ' '.join(texts)
        
        if combined_text.strip():
            self.content.append({
                'url': url,
                'text': combined_text.strip(),
                'title': title_text,
                'depth': depth
            })
    
    def _get_links(self, soup, base_url):
        """Extract links from the page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            # Remove fragment identifier
            full_url = urldefrag(full_url)[0]
            
            # Only include links from the same domain
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.append(full_url)
        
        return links
    
    def scrape(self, start_url):
        """
        Scrape the URL and optionally follow links
        
        Depth levels:
        - depth=1: Only scrape the provided URL
        - depth=2: Scrape the URL + all links it contains (1 level deep)
        - depth=3: Scrape the URL + links + links from those pages (2 levels deep)
        - etc.
        """
        to_visit = [(start_url, 1)]  # (url, current_depth) - start at depth 1
        
        while to_visit:
            url, current_depth = to_visit.pop(0)
            
            if url in self.visited_urls or current_depth > self.max_depth:
                continue
            
            try:
                logger.info(f"Scraping URL: {url} (depth: {current_depth}/{self.max_depth})")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                self.visited_urls.add(url)
                
                soup = BeautifulSoup(response.content, 'html.parser')
                self._extract_text(soup, url, current_depth)
                
                # Add links for next depth level (if within limit)
                if current_depth < self.max_depth:
                    links = self._get_links(soup, url)
                    # Limit number of links per page to avoid excessive crawling
                    for link in links[:self.max_links_per_page]:
                        if link not in self.visited_urls:
                            to_visit.append((link, current_depth + 1))
                
                # Be respectful with delays
                time.sleep(settings.download_delay)
                
            except Exception as e:
                logger.warning(f"Error scraping {url}: {str(e)}")
                continue
        
        return self.content


class URLProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    def _run_scraper(self, url: str, max_depth: int, max_links_per_page: int = 20) -> List[Dict[str, Any]]:
        """Run the scraper in a thread-safe way"""
        scraper = URLScraper(max_depth=max_depth, max_links_per_page=max_links_per_page)
        return scraper.scrape(url)
    
    async def process(self, url: str, metadata: Dict[str, Any] = None) -> List[LangchainDocument]:
        try:
            max_depth = metadata.get('max_depth', settings.max_scrape_depth) if metadata else settings.max_scrape_depth
            max_links_per_page = metadata.get('max_links_per_page', settings.max_links_per_page) if metadata else settings.max_links_per_page
            
            # Run scraper in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                self.executor,
                self._run_scraper,
                url,
                max_depth,
                max_links_per_page
            )
            
            # Convert scraped content to documents
            documents = []
            for item in content:
                doc_metadata = {
                    'source': item['url'],
                    'url': item['url'],
                    'title': item['title'],
                    'depth': item['depth'],
                    **(metadata or {})
                }
                doc = LangchainDocument(
                    page_content=item['text'],
                    metadata=doc_metadata
                )
                documents.append(doc)
            
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            logger.info(f"Processed URL {url}: {len(chunks)} chunks from {len(content)} pages")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            raise