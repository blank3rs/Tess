# speech_recognition_module.py

import time
import speech_recognition as sr
import threading
from global_vars import recognizer, is_speaking, should_stop

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
