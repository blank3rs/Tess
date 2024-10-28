def check_web_search(content: str) -> bool:
    """
    Check if the response indicates a web search is needed.
    Now handles variations and removes false positives.
    """
    if not content:
        return False
        
    content = content.strip().lower()
    
    # Direct match for web_search
    if content == "web_search":
        return True
        
    # Check for common phrases indicating need for real-time data
    real_time_indicators = [
        "current price",
        "latest news",
        "right now",
        "today's",
        "weather",
        "stock price",
        "sports score"
    ]
    
    return any(indicator in content for indicator in real_time_indicators)
    
