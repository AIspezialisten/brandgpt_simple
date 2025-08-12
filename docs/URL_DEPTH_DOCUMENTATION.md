# URL Ingestion Depth Parameter

This document describes the depth parameter feature for URL ingestion in the BrandGPT system.

## Overview

The depth parameter controls how many levels of links to follow during web scraping. This allows you to scrape not just a single URL, but also the pages it links to, creating a more comprehensive knowledge base from web content.

## How It Works

### Depth Levels

- **depth=1**: Only scrape the provided URL (default behavior)
- **depth=2**: Scrape the provided URL + all pages it links to (1 level deep)
- **depth=3**: Scrape the provided URL + linked pages + pages those link to (2 levels deep)
- **depth=4+**: Continue following links up to the specified depth

### Example

If you provide `https://example.com/page1` with depth=3:

1. **Depth 1**: Scrapes `https://example.com/page1`
2. **Depth 2**: Scrapes all pages linked from page1 (e.g., `https://example.com/page2`, `https://example.com/page3`)
3. **Depth 3**: Scrapes all pages linked from page2 and page3

## API Usage

### Using the REST API

```bash
curl -X POST "http://localhost:9700/api/ingest/url" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "url": "https://example.com",
    "content_type": "url",
    "max_depth": 2
  }'
```

### Schema

```json
{
  "session_id": "string",
  "content_type": "url",
  "url": "string",
  "max_depth": 1-10  // Optional, defaults to 1
}
```

## Configuration

### Environment Variables

You can configure default behavior using these environment variables:

```bash
# Default depth when not specified in API call
MAX_SCRAPE_DEPTH=1

# Maximum number of links to follow per page (prevents excessive crawling)
MAX_LINKS_PER_PAGE=20

# Delay between requests (seconds) - be respectful to target servers
DOWNLOAD_DELAY=0.5
```

### Settings File

In `brandgpt/config/settings.py`:

```python
class Settings(BaseSettings):
    # URL Scraping Configuration
    max_scrape_depth: int = Field(default=1, env="MAX_SCRAPE_DEPTH")
    max_links_per_page: int = Field(default=20, env="MAX_LINKS_PER_PAGE")
    download_delay: float = Field(default=0.5, env="DOWNLOAD_DELAY")
```

## Important Considerations

### Performance Impact

- Higher depth values will significantly increase processing time
- More pages mean more content to process and store
- Network requests increase exponentially with depth

### Recommended Depths

- **depth=1**: Single page analysis (fastest)
- **depth=2**: Small website sections (moderate performance)
- **depth=3**: Comprehensive documentation sites (slower)
- **depth=4+**: Use with caution, only for small sites

### Limitations

- Only follows links within the same domain (prevents crawling the entire web)
- Limited to `max_links_per_page` links per page (default: 20)
- Maximum depth is capped at 10 via API validation
- Respects `download_delay` between requests

## Testing

You can test the depth parameter functionality using the provided test script:

```bash
python test_url_pipeline.py
```

This will run tests with different depth values and show the results.

## Example Use Cases

### Documentation Sites
```json
{
  "url": "https://docs.example.com/getting-started",
  "max_depth": 3
}
```
Scrapes the getting started page plus linked documentation pages.

### Blog Analysis
```json
{
  "url": "https://blog.example.com/category/technology",
  "max_depth": 2
}
```
Scrapes the category page plus individual blog posts.

### Product Information
```json
{
  "url": "https://company.com/products/widget",
  "max_depth": 2
}
```
Scrapes the main product page plus related product pages.

## Monitoring and Debugging

### Log Messages

The scraper provides detailed logging:

```
INFO - Scraping URL: https://example.com/page1 (depth: 1/3)
INFO - Scraping URL: https://example.com/page2 (depth: 2/3)
INFO - Processed URL https://example.com: 15 chunks from 3 pages
```

### Content Metadata

Each scraped page includes metadata:

```json
{
  "source": "https://example.com/page1",
  "url": "https://example.com/page1",
  "title": "Page Title",
  "depth": 1,
  "document_id": 123,
  "session_id": "session-uuid"
}
```

## Best Practices

1. **Start Small**: Begin with depth=1, increase only if needed
2. **Test First**: Use the test script to verify behavior
3. **Monitor Performance**: Watch processing times and storage usage
4. **Respect Robots.txt**: Ensure you have permission to scrape target sites
5. **Use Appropriate Delays**: Don't overload target servers

## Troubleshooting

### Common Issues

1. **Slow Processing**: Reduce depth or max_links_per_page
2. **No Links Found**: Check if target site uses JavaScript navigation
3. **Access Denied**: Some sites block automated requests
4. **Memory Usage**: Large depths can consume significant memory

### Error Messages

- `depth > self.max_depth`: Link skipped due to depth limit
- `Error scraping {url}`: Network or parsing error for specific URL
- `Processing timeout`: Increase wait time for complex sites