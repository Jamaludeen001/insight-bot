from .audio_utils import get_voice_input

def get_user_input():
    """Handle user input selection and processing"""
    print("1. Text Input")
    print("2. Voice Input")
    
    while True:
        choice = input("\nSelect input method (1/2): ").strip()
        if choice in ["1", "2"]:
            break
        print("Invalid choice. Please select 1 for text or 2 for voice input.")
    
    if choice == "1":
        return input("Please provide your feedback: ")
    else:
        return get_voice_input()