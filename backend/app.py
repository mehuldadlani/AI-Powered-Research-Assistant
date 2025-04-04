import logging
from logging.handlers import RotatingFileHandler
import os
from quart import Quart
from src.api.routes import api, init_services
from src.config import Config
from src.services.rag_service import RAGService
from src.services.paper_search_service import PaperSearchService
from src.services.qna_service import QnAService
from src.services.crew_service import CrewAIService
from src.services.ai_service import AIService
from src.services.pdf_service import PDFService

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    file_handler = RotatingFileHandler('app.log', maxBytes=10000000, backupCount=5)
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

app = Quart(__name__)
Config.init_app(app)

rag_service = None
crew_service = None
paper_search_service = None
qna_service = None
ai_service = None
pdf_service = None

@app.before_serving
async def startup():
    global rag_service, crew_service, paper_search_service, qna_service, ai_service, pdf_service
    logger.info("Starting up the application...")
    try:
        Config.validate() 
        logger.info("Configuration validated successfully")

        rag_service = RAGService()
        await rag_service.initialize()
        logger.info("RAG service initialized successfully")
        
        crew_service = CrewAIService()
        await crew_service.initialize()
        logger.info("CrewAIService initialized successfully")
        
        paper_search_service = PaperSearchService(rag_service, crew_service)
        await paper_search_service.initialize()
        logger.info("PaperSearchService initialized successfully")
        
        qna_service = QnAService(rag_service, crew_service)
        await qna_service.initialize()
        logger.info("QnAService initialized successfully")
        
        ai_service = AIService(crew_service)
        await ai_service.initialize()
        logger.info("AIService initialized successfully")
        
        pdf_service = PDFService()
        await pdf_service.initialize()
        logger.info("PDFService initialized successfully")
        
        init_services(rag_service, crew_service, paper_search_service, qna_service, ai_service, pdf_service)
        logger.info("Services initialized and passed to routes")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        raise

@app.after_serving
async def shutdown():
    logger.info("Shutting down the application...")
    try:
        if rag_service:
            await rag_service.cleanup()
            logger.info("RAG service cleaned up successfully")
        if paper_search_service:
            await paper_search_service.cleanup()
            logger.info("PaperSearchService cleaned up successfully")
        if qna_service:
            await qna_service.cleanup()
            logger.info("QnAService cleaned up successfully")
        if crew_service:
            await crew_service.cleanup()
            logger.info("CrewAIService cleaned up successfully")
        if ai_service:
            await ai_service.cleanup()
            logger.info("AIService cleaned up successfully")
        if pdf_service:
            await pdf_service.cleanup()
            logger.info("PDFService cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)

app.register_blueprint(api)

if __name__ == "__main__":
    try:
        app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
    except Exception as e:
        logger.critical(f"Unhandled exception in main app: {str(e)}", exc_info=True)