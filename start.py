#!/usr/bin/env python3
"""
Simple startup script for the system
"""

import subprocess
import time
import webbrowser
import os

print("="*60)
print("  Starting Smart E-Commerce Search System")
print("="*60)
print()

# Start backend
print("Starting Backend API...")
backend = subprocess.Popen(['python', 'app.py'])
print("✅ Backend started (PID: {})".format(backend.pid))
print()

# Wait for backend to initialize
print("Waiting for backend to initialize...")
time.sleep(3)
print()

# Open frontend in browser
print("Opening Frontend in browser...")
frontend_path = os.path.abspath('index.html')
webbrowser.open('file:///' + frontend_path)
print("✅ Frontend opened")
print()

print("="*60)
print("  SYSTEM STARTED!")
print("="*60)
print()
print("Backend API: http://127.0.0.1:5000")
print("Frontend: Opened in browser")
print()
print("Press Ctrl+C to stop")
print()

try:
    backend.wait()
except KeyboardInterrupt:
    print("\n\nStopping system...")
    backend.terminate()
    print("✅ System stopped")


