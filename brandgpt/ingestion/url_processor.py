from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangchainDocument
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)


# URLScraper class removed - using LangChain's AsyncHtmlLoader instead


class URLProcessor:
    """
    URL processor using LangChain's AsyncHtmlLoader and Html2TextTransformer.

    These tools automatically:
    - Extract main content from web pages
    - Remove navigation, headers, footers, and boilerplate
    - Handle content much better than manual BeautifulSoup parsing
    """

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        # Html2TextTransformer for intelligent content extraction
        self.html2text = Html2TextTransformer()

    async def process(self, url: str, metadata: Dict[str, Any] = None) -> List[LangchainDocument]:
        """
        Process a URL using LangChain's AsyncHtmlLoader and Html2TextTransformer.

        Note: Currently processes single URL only (max_depth parameter ignored).
        For multi-page crawling, use RecursiveUrlLoader in the future.
        """
        try:
            logger.info(f"Loading URL: {url}")

            # Use LangChain's AsyncHtmlLoader to fetch the page
            loader = AsyncHtmlLoader([url], verify_ssl=True)
            docs = loader.load()

            if not docs:
                raise ValueError(f"No content loaded from URL: {url}")

            logger.info(f"✅ Loaded {len(docs)} page(s) from {url}")

            # Transform HTML to clean text using Html2TextTransformer
            # This automatically:
            # - Extracts main content
            # - Removes navigation, headers, footers
            # - Removes boilerplate and ads
            # - Converts to clean markdown-like text
            logger.info(f"Transforming HTML to text (removing navigation/boilerplate)...")
            docs = self.html2text.transform_documents(docs)

            # Log content size
            total_chars = sum(len(doc.page_content) for doc in docs)
            logger.info(f"✅ Extracted {total_chars} characters of main content")

            # Add custom metadata
            for doc in docs:
                doc.metadata.update({
                    'source': url,
                    'url': url,
                    **(metadata or {})
                })

            # Split documents into chunks
            chunks = self.text_splitter.split_documents(docs)

            logger.info(f"✅ Processed URL {url}: {len(chunks)} chunks from {len(docs)} page(s)")
            logger.info(f"   Chunk count reduced from previous implementation due to better content extraction")

            return chunks

        except Exception as e:
            logger.error(f"❌ Error processing URL {url}: {str(e)}")
            logger.error(f"   Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            raise