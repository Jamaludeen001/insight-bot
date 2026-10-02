import speech_recognition as sr

def get_voice_input():
    """Handle voice input and conversion to text"""
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print("\nListening... Speak your feedback")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10)
            
        try:
            text = recognizer.recognize_google(audio)
            print(f"\nRecognized text: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand audio. Please try again.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results: {e}")
            return None
    except Exception as e:
        print(f"Error accessing microphone: {e}")
        return None