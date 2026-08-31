"""
Vercel-compatible entry point for QVM Panel
This module wraps the Flask app for Vercel's serverless functions.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from avm import app, socketio

# Vercel expects a variable named 'app' or a handler function
# For Flask, we export the app object
