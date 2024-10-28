# response_generation.py

import threading
import speech_recognition as sr
from global_vars import llm_client, is_generating, should_stop, current_conversation

def generate_response(system_prompt, content):
    try:
        is_generating.set()
        should_stop.clear()

        # Format the system prompt and user input properly
        system_message = {"role": "system", "content": system_prompt}
        user_message = {"role": "user", "content": content}
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

            # Generate response with properly formatted messages
            messages = [system_message] + current_conversation[-5:]
            
            response = llm_client.chat.completions.create(
                model="local-model",
                messages=messages,
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
