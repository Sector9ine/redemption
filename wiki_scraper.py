import aiohttp
import asyncio
import json
import time
from bs4 import BeautifulSoup
import re
from typing import List, Dict

class AsyncWikiScraper:
    def __init__(self, base_url="https://redemptionps.com/wiki", max_concurrent=10):
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_all_pages(self) -> List[Dict]:
        """Get list of all wiki pages asynchronously"""
        pages = []
        apcontinue = None
        
        while True:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'allpages',
                'aplimit': '500'
            }
            if apcontinue:
                params['apcontinue'] = apcontinue
                
            async with self.session.get(f"{self.base_url}/api.php", params=params) as response:
                data = await response.json()
                
                if 'query' in data and 'allpages' in data['query']:
                    pages.extend(data['query']['allpages'])
                
                if 'continue' in data and 'apcontinue' in data['continue']:
                    apcontinue = data['continue']['apcontinue']
                else:
                    break
                    
        return pages
    
    async def get_page_content(self, page_title: str) -> str:
        """Get content of a specific page asynchronously"""
        params = {
            'action': 'parse',
            'format': 'json',
            'page': page_title,
            'prop': 'text',
            'section': 0
        }
        
        try:
            async with self.session.get(f"{self.base_url}/api.php", params=params) as response:
                data = await response.json()
                
                if 'parse' in data and 'text' in data['parse']:
                    # Extract text content from HTML
                    soup = BeautifulSoup(data['parse']['text']['*'], 'html.parser')
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    # Get text
                    text = soup.get_text()
                    # Clean up whitespace
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text
                
                return None
        except Exception as e:
            print(f"Error getting content for {page_title}: {e}")
            return None
    
    async def scrape_page_batch(self, pages_batch: List[Dict]) -> List[Dict]:
        """Scrape a batch of pages concurrently"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def scrape_single_page(page):
            async with semaphore:
                content = await self.get_page_content(page['title'])
                if content and len(content) > 50:  # Only include pages with substantial content
                    return {
                        "title": page['title'],
                        "content": content,
                        "pageid": page['pageid']
                    }
                return None
        
        tasks = [scrape_single_page(page) for page in pages_batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            elif isinstance(result, Exception):
                print(f"Exception occurred: {result}")
        
        return valid_results
    
    async def scrape_all_content(self) -> List[Dict]:
        """Scrape all wiki content asynchronously"""
        print("Getting list of all pages...")
        pages = await self.get_all_pages()
        print(f"Found {len(pages)} pages")
        
        training_data = []
        batch_size = 50  # Process pages in batches
        
        for i in range(0, len(pages), batch_size):
            batch = pages[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(pages) + batch_size - 1)//batch_size} (pages {i+1}-{min(i+batch_size, len(pages))})")
            
            batch_results = await self.scrape_page_batch(batch)
            training_data.extend(batch_results)
            
            # Small delay between batches to be respectful
            await asyncio.sleep(1)
        
        return training_data
    
    def save_training_data(self, data: List[Dict], filename: str = "wiki_training_data.json"):
        """Save training data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(data)} pages to {filename}")

async def main():
    """Main async function to run the scraper"""
    async with AsyncWikiScraper() as scraper:
        training_data = await scraper.scrape_all_content()
        scraper.save_training_data(training_data)

if __name__ == "__main__":
    asyncio.run(main())
