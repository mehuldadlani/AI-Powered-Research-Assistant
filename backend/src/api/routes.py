import logging
from functools import wraps
from src.config import Config
from quart import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from src.services.pdf_service import PDFService
from src.services.rag_service import RAGService
from src.services.ai_service import AIService
from src.services.paper_search_service import PaperSearchService
from src.services.qna_service import QnAService
from src.services.crew_service import CrewAIService

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)

# These should be initialized in app.py and passed to the blueprint
rag_service = None
crew_service = None
paper_search_service = None
qna_service = None
ai_service = None
pdf_service = None
extract_text_from_pdf = None
is_valid_pdf = None
summarize_text = None

def init_services(rag, crew, paper_search, qna, ai, pdf):
    global rag_service, crew_service, paper_search_service, qna_service, ai_service, pdf_service, extract_text_from_pdf, is_valid_pdf, summarize_text
    rag_service = rag
    crew_service = crew
    paper_search_service = paper_search
    qna_service = qna
    ai_service = ai
    pdf_service = pdf
    extract_text_from_pdf = pdf_service.extract_text_from_pdf
    is_valid_pdf = pdf_service.is_valid_pdf
    summarize_text = ai_service.summarize_text
    
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def validate_input(required_fields):
    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            data = await request.json
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            return await f(*args, **kwargs)
        return decorated_function
    return decorator


@api.route('/upload', methods=['POST'])
async def upload_file():
    files = await request.files
    if 'file' not in files:
        logger.warning("Upload attempt with no file part")
        return jsonify({"error": "No file part"}), 400
    
    file = files['file']
    if file.filename == '':
        logger.warning("Upload attempt with no selected file")
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        await file.save(filepath)
        
        try:
            if not await pdf_service.is_valid_pdf(filepath):
                logger.warning(f"Invalid PDF file attempted: {filename}")
                os.remove(filepath)
                return jsonify({"error": "Invalid or corrupted PDF file"}), 400
            
            text = await pdf_service.extract_text_from_pdf(filepath)
            if not text:
                logger.warning(f"No text extracted from PDF: {filename}")
                os.remove(filepath)
                return jsonify({"error": "No text could be extracted from the PDF"}), 400

            content_hash = rag_service.compute_content_hash(text)
            existing_doc = await rag_service.get_document_by_content_hash(content_hash)

            if existing_doc:
                logger.info(f"File already exists in the system: {existing_doc['id']}")
                return jsonify({
                    "message": "File already exists in the system",
                    "doc_id": existing_doc['id'],
                    "original_filename": filename,
                    "chunks": existing_doc.get('chunks', 0)
                }), 200

            # Store document in RAG service
            doc_id, is_new, doc_info = await rag_service.store_document(text, filename)

            # Process document
            with open(filepath, 'rb') as f:
                file_content = f.read()
            splits = await qna_service.process_document(file_content, doc_id)
            
            # Update the document with the number of chunks
            await rag_service.update_document_metadata(doc_id, {'chunks': len(splits)})
            
            action = "stored" if is_new else "updated"
            logger.info(f"File uploaded and {action}: {doc_id}")
            return jsonify({
                "message": f"File uploaded and {action}",
                "doc_id": doc_id,
                "original_filename": filename,
                "chunks": len(splits)
            }), 200
        except FileNotFoundError:
            logger.error(f"File not found after saving: {filepath}")
            return jsonify({"error": "File not found after upload"}), 500
        except ValueError as ve:
            logger.warning(f"Value error processing file: {str(ve)}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            logger.exception(f"Error processing uploaded file: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500
    
    logger.warning(f"Invalid file type attempted: {file.filename}")
    return jsonify({"error": "Invalid file type"}), 400

@api.route('/ask_question', methods=['POST'])
@validate_input(['question'])
async def ask_question():
    global qna_service
    data = await request.json
    question = data['question']
    doc_id = data.get('doc_id')  # This will be None if not provided
    
    try:
        if qna_service is None:
            raise ValueError("QnAService is not initialized")
        
        full_answer = await qna_service.answer_question(question, doc_id)
        
        # Extract only the answer part
        if isinstance(full_answer, dict):
            answer = full_answer.get('answer') or full_answer.get('result', str(full_answer))
        else:
            answer = str(full_answer)
        
        
        response = {"answer": answer}
        return jsonify(response), 200
    except ValueError as ve:
        logger.error(f"Value error: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception(f"Error answering question: {str(e)}")
        return jsonify({"error": "An unexpected error occurred while processing your question"}), 500
    
    
@api.route('/summarize', methods=['POST'])
@validate_input(['doc_id'])
async def summarize():
    data = await request.json
    doc_id = data['doc_id']
    level = data.get('level', 'intermediate')

    if level not in Config.ALLOWED_LEVELS:
        logger.warning(f"Invalid summarization level requested: {level}")
        return jsonify({"error": "Invalid summarization level"}), 400

    try:
        text = await rag_service.retrieve_document(doc_id)
        if not text:
            logger.error(f"Document not found in RAG: {doc_id}")
            return jsonify({"error": "Document not found"}), 404

        summary = await ai_service.summarize_text(text, level)
        logger.info(f"Successfully summarized document: {doc_id}")
        return jsonify({"summary": summary}), 200
    except Exception as e:
        logger.exception(f"Error during summarization: {str(e)}")
        return jsonify({"error": "An error occurred during summarization"}), 500
    

@api.route('/search_papers', methods=['POST'])
@validate_input(['query'])
async def search_papers():
    data = await request.json
    query = data['query']
    
    try:
        results = await paper_search_service.search_papers(query)
        return jsonify({"results": results}), 200
    except Exception as e:
        logger.exception(f"Error searching papers: {str(e)}")
        return jsonify({"error": "Error searching papers"}), 500

@api.route('/search_author', methods=['POST'])
@validate_input(['author_name'])
async def search_author():
    data = await request.json
    author_name = data['author_name']
    summarize = data.get('summarize', False)
    level = data.get('level', 'intermediate')
    
    if level not in Config.ALLOWED_LEVELS:
        logger.warning(f"Invalid summarization level requested: {level}")
        return jsonify({"error": "Invalid summarization level"}), 400
    
    try:
        results = await paper_search_service.search_author(author_name)
        
        if summarize:
            summary = await paper_search_service.summarize_author_profile(author_name, level)
            results['summary'] = summary
        
        return jsonify({"results": results}), 200
    except Exception as e:
        logger.exception(f"Error searching author: {str(e)}")
        return jsonify({"error": "Error searching author"}), 500

@api.route('/summarize_search', methods=['POST'])
@validate_input(['search_id'])
async def summarize_search():
    data = await request.json
    search_id = data['search_id']
    level = data.get('level', 'intermediate')
    
    if level not in Config.ALLOWED_LEVELS:
        logger.warning(f"Invalid summarization level requested: {level}")
        return jsonify({"error": "Invalid summarization level"}), 400
    
    try:
        text = await rag_service.retrieve_document(search_id)
        if not text:
            return jsonify({"error": "Search result not found"}), 404
        
        summary = await summarize_text(text, level)
        return jsonify({"summary": summary}), 200
    except Exception as e:
        logger.exception(f"Error summarizing search: {str(e)}")
        return jsonify({"error": "Error summarizing search"}), 500
    
@api.route('/test', methods=['GET'])
async def test():
    return jsonify({"message": "Test successful"}), 200

@api.route('/debug/services', methods=['GET'])
async def debug_services():
    return jsonify({
        "rag_service": str(rag_service),
        "crew_service": str(crew_service),
        "paper_search_service": str(paper_search_service),
        "qna_service": str(qna_service),
        "ai_service": str(ai_service),
        "pdf_service": str(pdf_service)
    }), 200