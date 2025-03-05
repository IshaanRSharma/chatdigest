from typing import Optional, Dict
import tiktoken
import re
import math

# Cache the encoders to avoid recreating them
_ENCODERS = {}

def get_tokenizer(model: Optional[str] = None):
    """
    Get a tokenizer for a specific model
    
    Args:
        model: The model name or encoding (default: cl100k_base)
        
    Returns:
        A tokenizer instance
    """
    encoding_name = model or "cl100k_base"  # cl100k_base works for many modern models
    
    # If the model is a specific model name, map it to an encoding
    if model:
        # Map model names to encoding names
        model_to_encoding = {
            # GPT-4 models
            "gpt-4": "cl100k_base",
            "gpt-4o": "cl100k_base",
            "gpt-4-turbo": "cl100k_base",
            "gpt-4-32k": "cl100k_base",
            
            # GPT-3.5 models
            "gpt-3.5-turbo": "cl100k_base",
            "gpt-3.5-turbo-16k": "cl100k_base",
            
            # Claude models - they use roughly the same tokenization as cl100k
            "claude-3-opus": "cl100k_base",
            "claude-3-sonnet": "cl100k_base",
            "claude-3-haiku": "cl100k_base",
            "claude-3.5-sonnet": "cl100k_base",
            "claude-3.7": "cl100k_base",
            
            # Other models
            "text-embedding-ada-002": "cl100k_base",
            
            # Older GPT models
            "text-davinci-003": "p50k_base",
            "text-davinci-002": "p50k_base",
            "text-davinci-001": "r50k_base",
            "text-curie-001": "r50k_base",
            "text-babbage-001": "r50k_base",
            "text-ada-001": "r50k_base",
            "davinci": "r50k_base",
            "curie": "r50k_base",
            "babbage": "r50k_base",
            "ada": "r50k_base",
            
            # Codex models
            "code-davinci-002": "p50k_base",
            "code-davinci-001": "p50k_base",
            "code-cushman-002": "p50k_base",
            "code-cushman-001": "p50k_base",
            
            # DeepSeek models
            "deepseek-7b": "cl100k_base",
            "deepseek-67b": "cl100k_base",
            
            # Gemini, Llama, etc. - fallback to cl100k as an approximation
            "gemini-pro": "cl100k_base",
            "gemini-1.5-pro": "cl100k_base",
            "llama-3-70b": "cl100k_base",
            "llama-3-8b": "cl100k_base",
            "mistral-large": "cl100k_base",
            "grok-v3": "cl100k_base",
        }
        
        encoding_name = model_to_encoding.get(model, "cl100k_base")
    
    # Get the tokenizer from cache or create a new one
    if encoding_name not in _ENCODERS:
        try:
            _ENCODERS[encoding_name] = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            # Fallback to cl100k_base if the requested encoding is not available
            print(f"Error loading tokenizer {encoding_name}: {e}")
            if encoding_name != "cl100k_base":
                if "cl100k_base" not in _ENCODERS:
                    _ENCODERS["cl100k_base"] = tiktoken.get_encoding("cl100k_base")
                return _ENCODERS["cl100k_base"]
            else:
                # If even cl100k_base fails, return None
                return None
    
    return _ENCODERS[encoding_name]

def estimate_tokens(text: str, model: Optional[str] = None) -> int:
    """
    Estimate the number of tokens in a text
    
    Args:
        text: The text to tokenize
        model: Optional model name to use for tokenization
        
    Returns:
        int: The estimated number of tokens
    """
    if not text:
        return 0
        
    try:
        # Try to use tiktoken with the appropriate encoder
        enc = get_tokenizer(model)
        if enc:
            return len(enc.encode(text))
        
    except Exception as e:
        print(f"Error estimating tokens: {e}")
    
    # 1. Word-based estimate (words are ~1.3 tokens on average)
    words = len(re.findall(r'\b\w+\b', text))
    word_estimate = words * 1.3
    
    # 2. Character-based estimate (chars are ~0.25 tokens on average)
    char_estimate = len(text) * 0.25
    
    # 3. Special tokens estimate (numbers, punctuation, etc.)
    special_chars = len(re.findall(r'[^\w\s]', text))
    
    combined_estimate = word_estimate + (special_chars * 0.5)
    
    # Use the larger of the estimates
    return math.ceil(max(combined_estimate, char_estimate))

def get_token_limit(llm_type: str) -> int:
    """
    Get the token limit for a specific LLM
    
    Args:
        llm_type: The LLM type identifier
        
    Returns:
        int: The token limit for the specified LLM
    """
    limits = {
        # OpenAI models
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-4o": 128000,
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        
        # Anthropic models
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "claude-3-haiku": 200000,
        "claude-3.5-sonnet": 200000,
        "claude-3.7": 200000,
        
        # Google models
        "gemini-pro": 30720,
        "gemini-1.5-pro": 1048576,  # 1M tokens
        
        # Meta (LLaMA) models
        "llama-3-70b": 8192,
        "llama-3-8b": 8192,
        "llama-2-70b": 4096,
        "llama-2-13b": 4096,
        "llama-2-7b": 4096,
        
        # Mistral models
        "mistral-large": 32000,
        "mistral-small": 32000,
        "mistral-7b": 8000,
        
        # DeepSeek models
        "deepseek-7b": 4096,
        "deepseek-67b": 4096,
        "deepseek-r1": 128000,
        # Grok models
        "grok-v3": 1000000,  
        
        # Cohere models
        "command-r": 128000,  
        "command-r-plus": 128000,  
        
        # Default fallback
        "default": 8000,
    }
    
    return limits.get(llm_type, 8000)  # Default to 4096 if unknown