# global_vars.py

import threading
import speech_recognition as sr
import pygame
from openai import OpenAI
import os
from dotenv import load_dotenv

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

# Global variables
is_speaking = threading.Event()
is_generating = threading.Event()
should_stop = threading.Event()
current_conversation = []  # Store conversation for current session

# Speech recognizer
recognizer = sr.Recognizer()
