# main.py

import requests
from speech_recognition_module import initialize_speech_recognition, speech_to_text
from text_to_speech_module import text_to_speech
from webSearcher import web_search
from response_generation import generate_response

def main():
    try:
        initialize_speech_recognition()
        conversation_context = []
        
        system_prompt = """
        <system>
        You are Jarvis, an AI assistant with real-time web search capabilitie!!!!!. Be direct, concise, and friendly.
        
        IMPORTANT INSTRUCTIONS FOR REAL-TIME INFORMATION:
        1. For ANY questions about:
           - Current events/news
           - Stock prices
           - Weather
           - Sports scores
           - Time-sensitive information
           - Facts that need verification
        2. Respond EXACTLY in this format when you need to search:
           web_search:your specific search query
        3. Make search queries specific and focused
        4. Do NOT provide outdated information - always use web search when unsure

        ****do not hallucinate use the web search for anything you dont know or are unsure about pls always use it when needed DO NTO ADD DATE UNLESS IS REQUIRED IN QUERY FOR REAL TIME JUST USE WORD: NOW****

    **************DONT TALKJK ABOUT YOURT LAST FUCKING UPDATE USE THE WEB SEARCH FOR EVERYTHING YOU DONT KNOW OR ARE UNSURE ABOUT PLS ALWAYS USE IT WHEN NEEDED **************
        ***** use the web search for everything you dont know or are unsure about pls always use it when needed *****
        </system>
        """

        initial_response = "Hey!"
        print("Jarvis:", initial_response)
        text_to_speech(initial_response)

        while True:
            result = speech_to_text()
            
            if result is None:
                continue
                
            if 'goodbye' in result.lower():
                farewell = "Goodbye! It was nice chatting with you!"
                print("Jarvis:", farewell)
                text_to_speech(farewell)
                break

            conversation_context.append({"role": "user", "content": result})
            
            # Get initial response
            response_text = generate_response(
                system_prompt + "\n\nPrevious conversation:\n" + 
                "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_context[-3:]]), 
                result
            ).strip('"')
            
            # Handle web search if needed
            if "web_search:" in response_text.lower():
                search_query = response_text.lower().split("web_search:", 1)[1].strip()
                print("🔍 Searching web for:", search_query)
                
                # Default to last 24 hours for time-sensitive queries
                time_period = 'd' if any(word in search_query.lower() for word in ['price', 'weather', 'score', 'news', 'stock']) else None
                try:
                    search_results = web_search(search_query, time_period=time_period)
                    print("Debug - Search Results:", search_results)  # Add debug print
                    
                    if search_results:
                        # Generate natural response using search results
                        new_prompt = f"""
                        <system>
                        You are a direct and accurate assistant. Using ONLY the information from the search results below,
                        provide a clear and concise response to the user's question. Do NOT add any information that isn't
                        in the search results. If the search results don't contain certain information, acknowledge that.
                        
                        User Question: {result}
                        Search Results: {search_results}
                        </system>


                        ****dont give me warnings and dont tell me its not correct just confidently give me the answer****
                        """
                        
                        response_text = generate_response(new_prompt, "Please provide a response based on these search results.").strip()
                    else:
                        response_text = "I tried searching for that information, but couldn't find reliable results. Could you try rephrasing your question?"
                except Exception as e:
                    print(f"Search error: {e}")
                    response_text = "I encountered an error while searching. Could you try asking in a different way?"
            
            # Handle the response
            if response_text.strip():
                print("Jarvis:", response_text)
                conversation_context.append({"role": "assistant", "content": response_text})
                text_to_speech(response_text)
            else:
                fallback = "I'm sorry, I couldn't process that properly. Could you rephrase?"
                print("Jarvis:", fallback)
                text_to_speech(fallback)

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please check your environment variables and internet connection.")

if __name__ == "__main__":
    main()
