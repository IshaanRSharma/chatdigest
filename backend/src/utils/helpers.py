import re
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

def extract_code_blocks(text: str, preserve_language: bool = True) -> List[str]:
    """
    Extract code blocks from text with improved pattern matching
    
    Args:
        text: The text containing code blocks
        preserve_language: Whether to preserve language specification in the output
        
    Returns:
        List[str]: Extracted code blocks with their markdown formatting
    """
    code_blocks = []
    
    # Match code blocks with language specification
    # Updated pattern to properly capture the content between triple backticks
    lang_pattern = r"```(\w+)?\s*\n([\s\S]*?)\n\s*```"
    lang_matches = re.findall(lang_pattern, text, re.DOTALL)
    
    # Handle language-specific code blocks
    for lang, content in lang_matches:
        if content.strip():  # Only include non-empty code blocks
            if preserve_language and lang:
                code_blocks.append(f"```{lang}\n{content.strip()}\n```")
            else:
                code_blocks.append(f"```\n{content.strip()}\n```")
    
    # Also look for inline code with backticks that might contain function calls or expressions
    # Only if they contain certain code-like syntax to avoid capturing emphasis
    inline_pattern = r"`([^`\n]{3,}?)`"
    inline_matches = re.findall(inline_pattern, text)
    
    for match in inline_matches:
        # Only include if it looks like code (has programming syntax)
        if re.search(r"[=(){}\[\]<>]|\w+\(", match) and match.strip():
            code_blocks.append(f"`{match.strip()}`")
    
    return code_blocks

def format_for_llm(content: str, target_llm: str) -> str:
    """
    Format content for a specific LLM
    
    Args:
        content: The content to format
        target_llm: The target LLM type
        
    Returns:
        str: The formatted content
    """
    # OpenAI format (GPT models)
    if target_llm.startswith("gpt-"):
        return content
    
    # Claude format (already Human: / Assistant:)
    elif target_llm.startswith("claude-"):
        return content
    
    # Gemini format (User: / Model:)
    elif target_llm.startswith("gemini-"):
        content = content.replace("Human:", "User:")
        content = content.replace("Assistant:", "Model:")
        return content
    
    # Other models - keep format as is
    else:
        return content

def generate_filename(target_llm: str, extension: str = "txt") -> str:
    """
    Generate a filename for the chat export
    
    Args:
        target_llm: The target LLM type
        extension: The file extension
        
    Returns:
        str: The generated filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"chatlog_synthesis_prompt_{target_llm}_{timestamp}.{extension}"

def get_llm_types() -> List[Dict[str, Any]]:
    """
    Get a list of supported LLM types with their properties
    
    Returns:
        List[Dict[str, Any]]: List of LLM types
    """
    return [
        # OpenAI models
        {"id": "gpt-4o", "name": "GPT-4o", "token_limit": 128000, "format": "openai", "recommended": True},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "token_limit": 128000, "format": "openai"},
        {"id": "gpt-4", "name": "GPT-4", "token_limit": 8192, "format": "openai"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "token_limit": 16384, "format": "openai"},
        
        # Anthropic models
        {"id": "claude-3.7-sonnet", "name": "Claude 3.7", "token_limit": 200000, "format": "anthropic", "recommended": True},
        {"id": "claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "token_limit": 200000, "format": "anthropic"},
        {"id": "claude-3-opus", "name": "Claude 3 Opus", "token_limit": 200000, "format": "anthropic"},
        {"id": "claude-3-haiku", "name": "Claude 3 Haiku", "token_limit": 20000, "format": "anthropic"},
        
        # Google models
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "token_limit": 1000000, "format": "google", "recommended": True},
        {"id": "gemini-pro", "name": "Gemini Pro", "token_limit": 32000, "format": "google"},
        
        # Open source models
        {"id": "llama-3-70b", "name": "Llama 3 70B", "token_limit": 8192, "format": "meta", "recommended": True},
        {"id": "llama-3-8b", "name": "Llama 3 8B", "token_limit": 8192, "format": "meta"},
        {"id": "mistral-large", "name": "Mistral Large", "token_limit": 32000, "format": "mistral", "recommended": True},
        {"id": "mistral-small", "name": "Mistral Small", "token_limit": 8000, "format": "mistral"},
        {"id": "grok-3", "name": "Grok-3", "token_limit": 1000000, "format": "xAI"},
        {"id": "deepseek-r1", "name": "DeepSeek R1", "token_limit": 128000, "format": "xAI"},
    ]
    