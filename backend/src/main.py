from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import tempfile
import os
from typing import Optional

from src.models.chat import SummaryRequest, SummaryResponse
from src.services.chat_parser import ChatParser
from src.services.token_counter import estimate_tokens, get_token_limit
from src.utils.helpers import extract_code_blocks, format_for_llm, generate_filename, get_llm_types
from src.services.ollama_service import OllamaService
from src.services.context_preserver import ContextPreserver


app = FastAPI(
    title="ChatDigest Server",
    description="Server for synthesizing chat logs for different LLM systems",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # nextjs connect 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
chat_parser = ChatParser()
context_preserver = ContextPreserver()
ollama_service = OllamaService(model="llama3.1:8b")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "ChatDigest API is running"}

@app.post("/api/parse")
async def parse_chat(file: Optional[UploadFile] = None, content: Optional[str] = Form(None)):
    """
    Parse a chat log from a file or direct content
    """
    try:
        # Get content from file or form data
        if file:
            file_content = await file.read()
            text_content = file_content.decode("utf-8")
        elif content:
            text_content = content
        else:
            raise HTTPException(status_code=400, detail="Either file or content must be provided")
        
        # Parse the chat log
        parsed_chat = chat_parser.parse(text_content)
        
        return {
            "content": text_content,
            "messages": [msg.dict() for msg in parsed_chat.messages],
            "message_count": parsed_chat.message_count,
            "token_count": parsed_chat.token_count,
            "format_detected": parsed_chat.format_detected
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Process an uploaded chat log file
    """
    try:
        content = await file.read()
        text_content = content.decode("utf-8")
        
        # Parse the chat log
        parsed_chat = chat_parser.parse(text_content)
        
        return {
            "content": text_content,
            "message_count": parsed_chat.message_count,
            "token_count": parsed_chat.token_count,
            "format_detected": parsed_chat.format_detected
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# @app.post("/api/summarize")
# async def summarize_chat(request: SummaryRequest):
#     """
#     Summarize a chat log for the target LLM
#     """
#     try:
#         # Parse the chat content
#         parsed_chat = chat_parser.parse(request.chat_content)
        
#         # Get token limit for the target LLM
#         token_limit = request.max_tokens or get_token_limit(request.target_llm)
        
#         # If already within limits, return as is
#         if parsed_chat.token_count <= token_limit * 0.9:  # 10% buffer
#             formatted_content = format_for_llm(request.chat_content, request.target_llm)
#             return {
#                 "summary": formatted_content,
#                 "original_tokens": parsed_chat.token_count,
#                 "summary_tokens": parsed_chat.token_count,
#                 "reduction": 0,
#                 "format": parsed_chat.format_detected
#             }
        
#         # Create a summary that preserves context
#         summary = create_context_preserving_summary(
#             parsed_chat.messages,
#             token_limit,
#             request.target_llm,
#             preserve_code=request.preserve_code,
#             include_system_prompts=request.include_system_prompts
#         )
        
#         # Format according to the target LLM
#         formatted_summary = format_for_llm(summary, request.target_llm)
        
#         # Count tokens in the summary
#         summary_tokens = estimate_tokens(formatted_summary, request.target_llm)
        
#         return {
#             "summary": formatted_summary,
#             "original_tokens": parsed_chat.token_count,
#             "summary_tokens": summary_tokens,
#             "reduction": round((parsed_chat.token_count - summary_tokens) / parsed_chat.token_count * 100, 1),
#             "format": parsed_chat.format_detected
#         }
    
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download")
async def download_summary(content: str = Form(...), filename: Optional[str] = Form(None)):
    """
    Generate a downloadable text file with the summarized content
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp:
            temp.write(content.encode("utf-8"))
            temp_path = temp.name
        
        # Generate a filename if not provided
        if not filename:
            filename = "previous_conversation_context.txt"
        
        # Return the file as a downloadable response
        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type="text/plain",
            background=lambda: os.remove(temp_path)  # Clean up the temp file afterward
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/llm-types")
async def get_available_llm_types():
    """
    Get a list of supported LLM types with their token limits
    """
    return {
        "llm_types": get_llm_types()
    }
    
@app.post("/api/compress-context")
async def compress_context(request: SummaryRequest):
    """
    Compress a chat log using Ollama and create a continuation prompt
    """
    try:
        # Parse the chat content
        parsed_chat = chat_parser.parse(request.chat_content)
        
        # Get token limit for the target LLM
        token_limit = request.max_tokens or get_token_limit(request.target_llm)
        
        # Check if Ollama service is available
        try:
            # Simple ping to check if Ollama is running
            ping_result = ollama_service.generate("Hello", {"num_predict": 5})
            ollama_available = True
        except Exception as e:
            print(f"Ollama service unavailable: {str(e)}")
            ollama_available = False
        
        # Process the chat with or without Ollama
        if ollama_available:
            # Split the messages for processing
            split_index = max(len(parsed_chat.messages) - 3, 3) # last 3 messages
            historical_messages = parsed_chat.messages[:split_index]
            recent_messages = parsed_chat.messages[split_index:]
            
            # Extract code blocks
            code_blocks = []
            for msg in parsed_chat.messages:
                from src.utils.helpers import extract_code_blocks
                blocks = extract_code_blocks(msg.content)
                code_blocks.extend(blocks)
            
            # Compress the historical part
            compressed_history = context_preserver.compress_with_llama(historical_messages, ollama_service)
            
            # Create the complete prompt
            final_prompt = context_preserver.create_summary_prompt(
                compressed_history, 
                recent_messages, 
                code_blocks, 
                request.target_llm
            )
        else:
            # Fallback to basic context preservation without Ollama
            raise HTTPException(status_code=503, detail=str(e))

        
        # Calculate token counts
        original_tokens = parsed_chat.token_count
        compressed_tokens = estimate_tokens(final_prompt, request.target_llm)
        return {
            "original_content": request.chat_content,
            "compressed_content": final_prompt,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "reduction_percentage": round((original_tokens - compressed_tokens) / original_tokens * 100, 1) if original_tokens > 0 else 0,
            "ollama_used": ollama_available
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
    
    