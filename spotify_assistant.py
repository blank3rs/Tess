import speech_recognition as sr
from dotenv import load_dotenv
import os
from pathlib import Path
from openai import OpenAI
import pygame
import io
import threading
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Initialize pygame mixer
pygame.mixer.init()

# Initialize conversation history
conversation_history = [
    {"role": "system", "content": "You are my friend. Keep conversations short and simple. Answer casually and don't try to sound smart. My name is Akshay, use it only when needed. Use slang, you can swear and be chill. Be human, you have had experiences, be relatable when needed but not too much. Really just be human, contribute, vent, talk to me. You can initiate your own convos when you feel like it, change topics, do whatever like a human."}
]

MAX_HISTORY_LENGTH = 10  # Reduced to keep only recent messages

def load_conversation_history():
    try:
        with open('conversation_history.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return conversation_history

def save_conversation_history():
    with open('conversation_history.json', 'w') as f:
        json.dump(conversation_history, f)

conversation_history = load_conversation_history()

def speech_to_text():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening... Speak now!")
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Reduced to 1 second
        
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=60)
        except sr.WaitTimeoutError:
            print("No speech detected. Please try again.")
            return None

    # Try Google Speech Recognition
    try:
        print("Recognizing speech...")
        text = recognizer.recognize_google(audio, language="en-US")
        print("You said:", text)
        return text
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")

    print("Speech recognition failed. Please try speaking more clearly or adjust your microphone.")
    return None

def text_to_speech(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    audio_stream = io.BytesIO(response.content)
    play_audio(audio_stream)

def play_audio(audio_stream):
    pygame.mixer.music.load(audio_stream)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(30)  # Increased tick rate for smoother playback

def generate_response(input_text):
    global conversation_history
    
    try:
        conversation_history.append({"role": "user", "content": input_text})
        
        # Keep only the most recent messages
        if len(conversation_history) > MAX_HISTORY_LENGTH + 1:  # +1 for the system message
            conversation_history = conversation_history[:1] + conversation_history[-(MAX_HISTORY_LENGTH):]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Updated to the latest model
            messages=conversation_history,
            max_tokens=150,  # Increased for slightly longer responses
            temperature=0.8  # Slightly increased for more varied responses
        )
        
        assistant_response = response.choices[0].message.content.strip()
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        # Save the updated conversation history
        save_conversation_history()
        
        return assistant_response
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm sorry, I couldn't generate a response at the moment."

# Example usage
if __name__ == "__main__":
    print("Welcome to the Spotify Assistant! Let's chat! (Say 'exit' to quit)")
    while True:
        print("\nListening for your input...")
        result = speech_to_text()
        if result:
            if result.lower() == 'exit':
                print("Goodbye!")
                break
            print("You said:", result)
            response_text = generate_response(result)
            print("Assistant:", response_text)
            text_to_speech(response_text)
