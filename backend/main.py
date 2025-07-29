"""
Main entry point for the FastAPI chat backend.

This module sets up and runs the FastAPI application with proper configuration
following conservative coding principles. It includes CORS setup for frontend
integration and basic health checking.
"""

import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

from src.api.chat import chat_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    This function sets up the FastAPI app with all necessary middleware
    and routes, following explicit configuration patterns.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="AI Chat Backend",
        description="A simple, reliable chat backend using FastAPI and LangChain",
        version="1.0.0"
    )
    
    # Configure CORS for frontend integration
    # In production, replace "*" with specific allowed origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "*"],  # Frontend dev server
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Simple health check endpoint."""
        return {"status": "healthy", "service": "chat-backend"}
    
    # Chat endpoint
    @app.post("/api/chat")
    async def chat_endpoint(request: Request):
        """
        Main chat endpoint that handles streaming conversations.
        
        This endpoint accepts messages in the format expected by the
        Vercel AI SDK and returns streaming responses.
        """
        return await chat_handler(request)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global exception handler for unexpected errors.
        
        This provides a consistent error response format and prevents
        sensitive information from leaking in error messages.
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "An internal server error occurred",
                "error_type": "internal_error"
            }
        )
    
    return app


def get_server_config() -> dict:
    """
    Get server configuration from environment variables.
    
    This function provides sensible defaults while allowing
    environment-based configuration for deployment flexibility.
    
    Returns:
        Dictionary of server configuration options
    """
    return {
        "host": os.getenv("HOST", "127.0.0.1"),
        "port": int(os.getenv("PORT", "8000")),
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "reload": os.getenv("ENVIRONMENT", "development") == "development"
    }


def main():
    """
    Main entry point for the application.
    
    This function creates the FastAPI app and starts the uvicorn server
    with appropriate configuration.
    """
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Validate required environment variables
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning(
                "OPENAI_API_KEY not found in environment. "
                "The chat functionality will not work until this is set."
            )
        
        # Create the FastAPI application
        app = create_app()
        
        # Get server configuration
        config = get_server_config()
        
        logger.info(f"Starting server on {config['host']}:{config['port']}")
        logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
        
        # Start the server
        uvicorn.run(
            "main:create_app",
            factory=True,
            **config
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
