import speech_recognition as sr
from dotenv import load_dotenv
import os
from pathlib import Path
from openai import OpenAI
import pygame
import io
import threading
import json
import time
from datetime import datetime
import webbrowser
import subprocess
import platform
import psutil
import requests
from bs4 import BeautifulSoup
import pyautogui
import sys
from urllib.parse import quote_plus
from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Initialize OpenAI client for TTS only
tts_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Add a new client for local LLM
llm_client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="not-needed"  # Local servers typically don't need an API key
)

# Initialize pygame mixer
pygame.mixer.init()

# Add a global variable for speech control
is_speaking = threading.Event()

# Add this as a global variable at the top of the file, after the other initializations
recognizer = sr.Recognizer()

# Add these new global variables after the existing ones
is_generating = threading.Event()
should_stop = threading.Event()

# Add this near the top with other global variables
current_conversation = []  # Store conversation for current session

# Add these function definitions after the existing imports
def load_conversation_history():
    default_system_prompt = {
        "role": "system",
        "content": """You are Jarvis, an AI assistant. Be direct, concise, and helpful. 
        Use casual language and be modern and human-like."""
    }
    
    # Simply return default prompt and empty list - no file loading
    return default_system_prompt, []

def save_conversation_history(system_prompt, current_conversation):
    # Remove this function's implementation since we're only keeping memory per run
    pass

def initialize_speech_recognition():
    global recognizer
    # Reduce timeouts and make recognition more responsive
    recognizer.phrase_time_limit = 10  # Reduced from 15
    recognizer.pause_threshold = 1.0   # Reduced from 3.0
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 300   # Increased for better voice detection
    recognizer.dynamic_energy_adjustment_damping = 0.1  # More responsive
    recognizer.dynamic_energy_ratio = 1.2  # More sensitive
    
    with sr.Microphone() as source:
        print("Adjusting for background noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=2)  # Reduced from 3

def speech_to_text():
    global recognizer
    try:
        with sr.Microphone() as source:
            print("Waiting for wake word 'jarvis'...")
            
            last_wake_time = time.time()
            in_conversation = True
            
            while True:
                try:
                    current_time = time.time()
                    
                    if in_conversation and (current_time - last_wake_time < 15):  # Reduced from 20
                        print("Listening...")
                        response_audio = recognizer.listen(
                            source,
                            timeout=8,        # Reduced from 12
                            phrase_time_limit=10  # Reduced from 15
                        )
                        
                        # Use faster recognition with less accuracy for wake word
                        response_text = recognizer.recognize_google(
                            response_audio,
                            language="en-US"
                        )
                        
                        print("You:", response_text)
                        last_wake_time = current_time
                        return response_text
                    
                    else:
                        in_conversation = False
                        audio = recognizer.listen(source, phrase_time_limit=3)  # Added limit for wake word
                        text = recognizer.recognize_google(audio, language="en-US").lower()
                        
                        if any(wake_word in text for wake_word in ['jarvis', 'jarv', 'travis', 'javis']):
                            print("Yes, I'm listening...")
                            last_wake_time = current_time
                            in_conversation = True
                            
                            response_audio = recognizer.listen(
                                source,
                                timeout=8,     # Reduced from 12
                                phrase_time_limit=10  # Reduced from 12
                            )
                            
                            response_text = recognizer.recognize_google(response_audio, language="en-US")
                            print("You:", response_text)
                            return response_text

                except sr.WaitTimeoutError:
                    if in_conversation and (current_time - last_wake_time >= 20):
                        print("Conversation window expired. Say 'Jarvis' to start a new conversation.")
                        in_conversation = False
                    continue
                except sr.UnknownValueError:
                    continue
                
    except Exception as e:
        print(f"Error with speech recognition: {e}")
        print("Please check your microphone.")

    return None

def text_to_speech(text):
    try:
        response = tts_client.audio.speech.create(
            model="tts-1", 
            voice="alloy",
            input=text
        )
        audio_stream = io.BytesIO(response.content)
        play_audio(audio_stream)
            
    except Exception as e:
        print(f"Error with text-to-speech: {e}")

def play_audio(audio_stream):
    is_speaking.set()
    should_stop.clear()
    pygame.mixer.music.load(audio_stream)
    pygame.mixer.music.play()
    
    def check_wake_word():
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 200
        recognizer.dynamic_energy_ratio = 1.5
        
        with sr.Microphone() as source:
            while pygame.mixer.music.get_busy() and is_speaking.is_set():
                try:
                    audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=1)
                    text = recognizer.recognize_google(audio, language="en-US").lower()
                    if any(wake_word in text for wake_word in ['jarvis', 'jarv', 'travis', 'javis']):
                        print("Stopping playback...")
                        is_speaking.clear()
                        should_stop.set()
                        pygame.mixer.music.stop()
                        return
                except (sr.WaitTimeoutError, sr.UnknownValueError):
                    continue
                except Exception as e:
                    continue

    wake_word_thread = threading.Thread(target=check_wake_word)
    wake_word_thread.daemon = True
    wake_word_thread.start()
    
    while pygame.mixer.music.get_busy() and is_speaking.is_set():
        pygame.time.Clock().tick(10)
    
    is_speaking.clear()
    wake_word_thread.join(timeout=0.5)

def generate_response(input_text, system_prompt, current_conversation):
    try:
        is_generating.set()
        should_stop.clear()
        
        # Format the user input
        user_message = {"role": "user", "content": input_text}
        current_conversation.append(user_message)
        
        try:
            # Create interrupt thread for handling wake word detection
            def check_interruption():
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    while is_generating.is_set():
                        try:
                            audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=1)
                            text = recognizer.recognize_google(audio, language="en-US").lower()
                            if any(wake_word in text for wake_word in ['jarvis', 'jarv', 'travis', 'javis']):
                                print("\nInterrupting generation...")
                                should_stop.set()
                                return
                        except (sr.WaitTimeoutError, sr.UnknownValueError):
                            continue
                        except Exception as e:
                            continue

            interrupt_thread = threading.Thread(target=check_interruption)
            interrupt_thread.daemon = True
            interrupt_thread.start()

            # Generate response
            response = llm_client.chat.completions.create(
                model="local-model",
                messages=[{"role": "system", "content": system_prompt["content"]}] + current_conversation[-5:],
                max_tokens=2000,
                temperature=0.7
            )
            
            if should_stop.is_set():
                is_generating.clear()
                return "I've stopped generating the response. What else can I help you with?"

            content = response.choices[0].message.content
            current_conversation.append({"role": "assistant", "content": content})
            return content
            
        except Exception as e:
            print(f"Error in response generation: {str(e)}")
            return "I encountered an error while processing your request. Could you try again?"
            
        finally:
            is_generating.clear()
            interrupt_thread.join(timeout=0.5)
            
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return "I'm having trouble processing that request. Could you try again?"

def main():
    try:
        print("Jarvis is online! Say 'Jarvis' to get my attention, then speak your question or command.")
        print("(Say 'Jarvis goodbye' to end our conversation)")

        # Initialize speech recognition once at startup
        initialize_speech_recognition()

        # Load conversation history
        system_prompt, current_conversation = load_conversation_history()

        initial_response = generate_response("Hello! I'm ready to help.", system_prompt, current_conversation)
        print("Jarvis:", initial_response)
        text_to_speech(initial_response)

        while True:
            result = speech_to_text()
            
            if result is None:
                continue

            if 'goodbye' in result.lower():
                farewell = "Goodbye! It was nice chatting with you. Call me whenever you need help!"
                print("Jarvis:", farewell)
                text_to_speech(farewell)
                break

            # Get the response
            response_text = generate_response(result, system_prompt, current_conversation)
            
            # Only print and speak if it's not a tool call
            if not ("<tool_call>" in response_text or "Goal:" in response_text):
                print("Jarvis:", response_text)
                text_to_speech(response_text)
            else:
                # For tool calls, just print "Searching..." and wait for final response
                print("Searching...")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please check your environment variables and internet connection.")

if __name__ == "__main__":
    main()
