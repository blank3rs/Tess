# text_to_speech_module.py

import pygame
import io
import threading
import speech_recognition as sr
from global_vars import tts_client, is_speaking, should_stop

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
