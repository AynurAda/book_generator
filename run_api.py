#!/usr/bin/env python3
"""
Script to run the Learner Book Generation API server.

Usage:
    python run_api.py

Or with uvicorn directly:
    uvicorn book_generator.api_server:app --reload --port 8000
"""

import uvicorn

if __name__ == "__main__":
    print("Starting Learner Book Generation API...")
    print("API docs available at: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/health")
    print()

    uvicorn.run(
        "book_generator.api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
