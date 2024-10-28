from googlesearch import search
import requests
from bs4 import BeautifulSoup
from response_generation import generate_response
from typing import Optional
from datetime import datetime, timedelta

def extract_text_from_url(url: str) -> str:
    """Extract readable text content from a URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
            
        text = soup.get_text(separator='\n', strip=True)
        return text[:3000]  # Limit text length
    except Exception as e:
        print(f"Error extracting text from {url}: {str(e)}")
        return None

def web_search(query: str, time_period: Optional[str] = None) -> str:
    """
    Search that gets first result and passes to LLM
    
    Args:
        query: Search query string
        time_period: Optional time filter ('h' for past hour, 'd' for past 24h, 
                    'w' for past week, 'm' for past month)
    """
    try:
        # Add time-based keywords for recent results
        time_sensitive_keywords = ['price', 'weather', 'score', 'news', 'stock']
        
        if any(keyword in query.lower() for keyword in time_sensitive_keywords):
            # Add time-specific terms to the query
            if time_period == 'h':
                search_query = f"{query} in the last hour"
            elif time_period == 'd':
                search_query = f"{query} today current"
            elif time_period == 'w':
                search_query = f"{query} this week"
            elif time_period == 'm':
                search_query = f"{query} this month"
            else:
                search_query = f"{query} current now today"
        else:
            search_query = query

        # Get search results
        results = list(search(
            search_query, 
            num_results=3  # Increased to 3 to have better chances of recent content
        ))
        
        if not results:
            return "No results found."

        # Try each URL until we get valid content
        content = None
        used_url = None
        
        for url in results:
            content = extract_text_from_url(url)
            if content:
                used_url = url
                break
                
        if not content:
            return "Couldn't extract content from any webpage."

        # Pass content to LLM with emphasis on current information
        prompt = f"""
        Based ONLY on this webpage content from {used_url}, provide a current and accurate answer to: '{query}'
        
        Webpage Content:
        {content}
        
        Important: Focus on the most recent information available in the content.
        If the information seems outdated, please indicate that clearly.
        """
        return generate_response(prompt, query)

    except Exception as e:
        return f"Search error: {str(e)}"
