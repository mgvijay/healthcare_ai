import os

# Centralized configuration for agents
# Use environment variable MODEL_NAME to override default model selection
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

# Default security code for protected operations (can be overridden via env)
SECURITY_CODE = os.getenv("SECURITY_CODE", "0864")
