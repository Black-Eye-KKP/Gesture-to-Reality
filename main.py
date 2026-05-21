"""
GestureControl — Hand Gesture Mouse & Touchpad Controller for Windows 11
Entry point. Run this file to launch the application.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        from ui.app import GestureControlApp
        app = GestureControlApp()
        app.run()
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        print("\nPlease install requirements:")
        print("  pip install -r requirements.txt")
        print("\nThen run: python main.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
