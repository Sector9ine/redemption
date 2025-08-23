import json
import re
from typing import List, Dict, Optional

class SQLWikiParser:
    def __init__(self, sql_file: str = "wiki.sql"):
        self.sql_file = sql_file
        
    def parse_sql_dump(self) -> List[Dict]:
        """Parse the SQL dump and extract wiki content"""
        print("Reading SQL dump file...")
        
        with open(self.sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("Extracting page data...")
        pages = self._extract_pages(sql_content)
        
        print("Extracting revision data...")
        revisions = self._extract_revisions(sql_content)
        
        print("Extracting text content...")
        texts = self._extract_texts(sql_content)
        
        print("Matching pages with content...")
        wiki_data = self._match_pages_with_content(pages, revisions, texts)
        
        return wiki_data
    
    def _extract_pages(self, sql_content: str) -> Dict[int, str]:
        """Extract page_id -> page_title mapping"""
        pages = {}
        
        # Find all INSERT INTO `page` statements
        page_inserts = re.findall(r'INSERT INTO `page`.*?;', sql_content, re.DOTALL | re.IGNORECASE)
        
        for insert in page_inserts:
            # Extract VALUES part
            values_match = re.search(r'VALUES\s*(.*?);', insert, re.DOTALL | re.IGNORECASE)
            if values_match:
                values_str = values_match.group(1)
                # Parse individual value tuples
                value_tuples = re.findall(r'\(([^)]+)\)', values_str)
                
                for tuple_str in value_tuples:
                    # Split by comma, but be careful with quoted strings
                    parts = self._split_sql_values(tuple_str)
                    if len(parts) >= 3:
                        try:
                            page_id = int(parts[0])
                            page_title = parts[2].strip("'")
                            # Only include main namespace pages (namespace = 0)
                            if parts[1] == '0':
                                pages[page_id] = page_title
                        except (ValueError, IndexError):
                            continue
        
        return pages
    
    def _extract_revisions(self, sql_content: str) -> Dict[int, int]:
        """Extract page_id -> latest_revision_id mapping"""
        revisions = {}
        
        # Find all INSERT INTO `revision` statements
        revision_inserts = re.findall(r'INSERT INTO `revision`.*?;', sql_content, re.DOTALL | re.IGNORECASE)
        
        for insert in revision_inserts:
            values_match = re.search(r'VALUES\s*(.*?);', insert, re.DOTALL | re.IGNORECASE)
            if values_match:
                values_str = values_match.group(1)
                value_tuples = re.findall(r'\(([^)]+)\)', values_str)
                
                for tuple_str in value_tuples:
                    parts = self._split_sql_values(tuple_str)
                    if len(parts) >= 2:
                        try:
                            rev_id = int(parts[0])
                            page_id = int(parts[1])
                            # Keep track of the latest revision for each page
                            if page_id not in revisions or rev_id > revisions[page_id]:
                                revisions[page_id] = rev_id
                        except (ValueError, IndexError):
                            continue
        
        return revisions
    
    def _extract_texts(self, sql_content: str) -> Dict[int, str]:
        """Extract text_id -> content mapping"""
        texts = {}
        
        # Find all INSERT INTO `text` statements
        text_inserts = re.findall(r'INSERT INTO `text`.*?;', sql_content, re.DOTALL | re.IGNORECASE)
        
        for insert in text_inserts:
            values_match = re.search(r'VALUES\s*(.*?);', insert, re.DOTALL | re.IGNORECASE)
            if values_match:
                values_str = values_match.group(1)
                value_tuples = re.findall(r'\(([^)]+)\)', values_str)
                
                for tuple_str in value_tuples:
                    parts = self._split_sql_values(tuple_str)
                    if len(parts) >= 2:
                        try:
                            text_id = int(parts[0])
                            content = parts[1].strip("'")
                            # Unescape common SQL escape sequences
                            content = content.replace("\\'", "'").replace('\\"', '"').replace('\\\\', '\\')
                            # Decode hexadecimal content if needed
                            content = self._decode_content(content)
                            texts[text_id] = content
                        except (ValueError, IndexError):
                            continue
        
        return texts
    
    def _decode_content(self, content: str) -> str:
        """Decode MediaWiki content from various encodings"""
        # Check if content is hexadecimal
        if content.startswith('0x'):
            try:
                # Remove '0x' prefix and decode hex
                hex_content = content[2:]
                # Convert hex to bytes, then decode as utf-8
                decoded = bytes.fromhex(hex_content).decode('utf-8', errors='ignore')
                return decoded
            except (ValueError, UnicodeDecodeError):
                return content
        
        # Check if content is base64 encoded
        if content.startswith('gzip:') or content.startswith('utf-8:'):
            # This would require additional decoding logic
            # For now, return as-is
            return content
        
        return content
    
    def _split_sql_values(self, value_string: str) -> List[str]:
        """Split SQL values by comma, respecting quoted strings"""
        parts = []
        current_part = ""
        in_quotes = False
        quote_char = None
        i = 0
        
        while i < len(value_string):
            char = value_string[i]
            
            if not in_quotes and char in ["'", '"']:
                in_quotes = True
                quote_char = char
                current_part += char
            elif in_quotes and char == quote_char:
                # Check for escaped quote
                if i + 1 < len(value_string) and value_string[i + 1] == quote_char:
                    current_part += char + char
                    i += 1
                else:
                    in_quotes = False
                    quote_char = None
                current_part += char
            elif not in_quotes and char == ',':
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
            
            i += 1
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts
    
    def _match_pages_with_content(self, pages: Dict[int, str], revisions: Dict[int, int], texts: Dict[int, str]) -> List[Dict]:
        """Match pages with their content using revision and text tables"""
        wiki_data = []
        
        print(f"Found {len(pages)} pages, {len(revisions)} revisions, {len(texts)} texts")
        
        for page_id, page_title in pages.items():
            if page_id in revisions:
                rev_id = revisions[page_id]
                # In MediaWiki, the text_id is typically the same as the revision_id
                if rev_id in texts:
                    content = texts[rev_id]
                    if content and len(content.strip()) > 0:
                        # Temporarily remove filtering to see what we get
                        wiki_data.append({
                            "title": page_title,
                            "content": content.strip(),
                            "url": f"https://redemptionps.com/wiki/{page_title.replace(' ', '_')}"
                        })
        
        print(f"Matched {len(wiki_data)} pages with content")
        return wiki_data
    
    def _is_system_page(self, title: str) -> bool:
        """Check if a page is a system page that should be excluded"""
        system_prefixes = [
            'MediaWiki:', 'Special:', 'Template:', 'Help:', 'User:', 
            'Talk:', 'User talk:', 'Template talk:', 'Help talk:',
            'File:', 'File talk:', 'Category:', 'Category talk:',
            'Wikipedia:', 'Wikipedia talk:', 'Portal:', 'Portal talk:',
            '0x'  # Exclude hex-encoded system pages
        ]
        
        for prefix in system_prefixes:
            if title.startswith(prefix):
                return True
        
        return False
    
    def save_to_json(self, data: List[Dict], filename: str = "wiki_training_data.json"):
        """Save the extracted data to JSON format"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(data)} pages to {filename}")

def main():
    parser = SQLWikiParser()
    wiki_data = parser.parse_sql_dump()
    parser.save_to_json(wiki_data)
    print(f"Successfully extracted {len(wiki_data)} wiki pages from SQL dump")

if __name__ == "__main__":
    main()
