import os
import secrets
from typing import Set, Dict, Any

class Config:
    # Debug mode (set to False in production)
    DEBUG: bool = os.getenv('FLASK_ENV', 'development') == 'development'

    # Server settings
    HOST: str = os.getenv('HOST', '127.0.0.1')
    PORT: int = int(os.getenv('PORT', '5001'))
    # File upload settings
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS: Set[str] = {'pdf'}
    MAX_CONTENT_LENGTH: int = int(os.getenv('MAX_CONTENT_LENGTH', str(16 * 1024 * 1024)))  # 16 MB default

    # RAG settings
    RAG_STORAGE_PATH: str = os.getenv('RAG_STORAGE_PATH', 'rag_db')
    CHROMA_DB_PATH: str = os.getenv('CHROMA_DB_PATH', './demo-rag-chroma')
    CHROMA_COLLECTION_NAME: str = os.getenv('CHROMA_COLLECTION_NAME', 'research_papers')

    # Paper search settings
    GOOGLE_SCHOLAR_MAX_RESULTS: int = int(os.getenv('GOOGLE_SCHOLAR_MAX_RESULTS', '20'))
    ARXIV_MAX_RESULTS: int = int(os.getenv('ARXIV_MAX_RESULTS', '20'))
    AUTHOR_TOP_CITED_COUNT: int = int(os.getenv('AUTHOR_TOP_CITED_COUNT', '20'))
    AUTHOR_RECENT_PAPERS_COUNT: int = int(os.getenv('AUTHOR_RECENT_PAPERS_COUNT', '20'))

    # AI settings
    ALLOWED_LEVELS: Set[str] = {'beginner', 'intermediate', 'expert'}
    SUMMARIZATION_TIMEOUT: int = int(os.getenv('SUMMARIZATION_TIMEOUT', '60'))  # seconds
    USE_SUMMARY_CACHE: bool = os.getenv('USE_SUMMARY_CACHE', 'True').lower() == 'true'
    SUMMARY_CACHE_SIZE: int = int(os.getenv('SUMMARY_CACHE_SIZE', '100'))
    CHUNK_SIZE = 400
    CHUNK_OVERLAP = 100

    # Ollama settings
    OLLAMA_BASE_URL: str = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL: str = os.getenv('OLLAMA_MODEL', 'mistral')
    OLLAMA_API_URL: str = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/embeddings')
    OLLAMA_EMBEDDING_MODEL: str = os.getenv('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text:latest')
    
    
    # CrewAI settings
    CREW_VERBOSE: bool = os.getenv('CREW_VERBOSE', 'False').lower() == 'true'

    # Secret key for session management (must be set in environment for production)
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        if DEBUG:
            SECRET_KEY = secrets.token_hex(32)
            print("WARNING: Using a random secret key. This is okay for development, but not for production.")
        else:
            raise ValueError("No SECRET_KEY set for Flask application in production mode")
        
        
    @classmethod
    def init_app(cls, app) -> None:
        # You can add application-wide configurations here
        app.config.from_object(cls)

        # Ensure necessary directories exist
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.RAG_STORAGE_PATH, exist_ok=True)
        os.makedirs(cls.CHROMA_DB_PATH, exist_ok=True)

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        return {key: value for key, value in cls.__dict__.items() 
                if not key.startswith('__') and not callable(value)}

    @classmethod
    def validate(cls) -> None:
        """Validate the configuration settings."""
        if cls.MAX_CONTENT_LENGTH <= 0:
            raise ValueError("MAX_CONTENT_LENGTH must be positive")
        if cls.SUMMARIZATION_TIMEOUT <= 0:
            raise ValueError("SUMMARIZATION_TIMEOUT must be positive")
        # Add more validation as needed