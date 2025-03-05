import re
import json
from typing import List, Dict, Any, Optional
import regex  # For more advanced regex patterns with overlapping

from src.models.chat import ChatMessage, ParsedChat
from src.services.token_counter import estimate_tokens

class ChatParser:
    """
    Service for parsing chat logs from different sources and formats
    """
    
    def parse(self, content: str, specified_format: Optional[str] = None) -> ParsedChat:
        """
        Parse a chat log using either the specified format or auto-detection
        
        Args:
            content: The raw chat log content
            specified_format: Optional format to use instead of auto-detection
            
        Returns:
            ParsedChat: Structured representation of the chat
        """
        # Use specified format if provided, otherwise detect
        format_to_use = specified_format if specified_format else self._detect_format(content)
        
        # Parse according to the format
        # if format_to_use == "json":
        #     messages = self._parse_json_format(content)
        # elif format_to_use == "openai_web":
        #     messages = self._parse_openai_web_format(content)
        # elif format_to_use == "said_format":
        #     messages = self._parse_said_format(content)
        # elif format_to_use == "conversation":
        #     messages = self._parse_conversation_format(content)
        # else:
        if format_to_use == "said_format":
            messages = self._parse_said_format(content)
        else:
            messages = self._parse_generic_format(content)
        
        # Count tokens
        token_count = estimate_tokens(content)
        
        return ParsedChat(
            messages=messages,
            format_detected=format_to_use,
            token_count=token_count,
            message_count=len(messages),
            raw_content=content
        )
    
    def _detect_format(self, content: str) -> str:
        """
        Detect the format of the chat log
        
        Args:
            content: The raw chat log content
            
        Returns:
            str: The detected format
        """
        # Check for JSON format
        if content.strip().startswith("{") or content.strip().startswith("["):
            try:
                json.loads(content)
                return "json"
            except json.JSONDecodeError:
                pass
        
        # Check for "You said:" / "ChatGPT said:" format
        said_pattern = r"(You|ChatGPT|Claude|Gemini|Grok|Bard|AI|Assistant)\s+said:"
        if re.search(said_pattern, content, re.IGNORECASE | re.MULTILINE):
            return "said_format"
        
        
        # Check for OpenAI web format with markdown headers
        openai_pattern = r"(#\s+\w+\s*\n+[\s\S]*?)(?=#\s+\w+|$)"
        if re.search(openai_pattern, content):
            return "openai_web"
        
        # Check for general conversation format (User: / AI:, etc.)
        conversation_pattern = r"(User|Human|Person|Customer|AI|Bot|Assistant|System):\s"
        if re.search(conversation_pattern, content, re.MULTILINE):
            return "conversation"
        
        # Default to generic
        return "generic"
    
    def _parse_json_format(self, content: str) -> List[ChatMessage]:
        """
        Parse JSON-formatted chat logs (like OpenAI API format)
        """
        try:
            parsed = json.loads(content)
            
            # Handle array of messages
            if isinstance(parsed, list):
                messages = []
                for msg in parsed:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        messages.append(ChatMessage(
                            role=msg["role"],
                            content=msg["content"]
                        ))
                return messages
            
            # Handle object with messages array
            elif isinstance(parsed, dict) and "messages" in parsed:
                messages = []
                for msg in parsed["messages"]:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        messages.append(ChatMessage(
                            role=msg["role"],
                            content=msg["content"]
                        ))
                return messages
            
            # Handle object with conversation or similar field
            elif isinstance(parsed, dict):
                for field in ["conversation", "chat", "dialogue", "transcript"]:
                    if field in parsed and isinstance(parsed[field], list):
                        messages = []
                        for msg in parsed[field]:
                            if isinstance(msg, dict):
                                role = msg.get("role", msg.get("speaker", "unknown"))
                                content = msg.get("content", msg.get("text", msg.get("message", "")))
                                if content:
                                    messages.append(ChatMessage(role=role, content=content))
                        if messages:
                            return messages
            
            # If we couldn't parse it properly, return as a single user message
            return [ChatMessage(role="user", content=content)]
            
        except Exception as e:
            # If JSON parsing fails entirely, fall back to generic
            return self._parse_generic_format(content)
    
    
    def _parse_said_format(self, content: str) -> List[ChatMessage]:
        """
        Parse "You said:" / "ChatGPT said:" format
        """
        messages = []
        
        # This pattern finds blocks starting with "X said:" and captures everything until the next "X said:" or end
        pattern = r"(You|ChatGPT|Claude|Gemini|Grok|Bard|AI|Assistant)\s+said:(.*?)(?=(?:You|ChatGPT|Claude|Gemini|Grok|Bard|AI|Assistant)\s+said:|$)"
        matches = re.findall(pattern, content, re.DOTALL)
        
        # Check if the first line is missing a label
        lines = content.strip().split("\n")
        first_line = lines[0].strip() if lines else ""

        # If the first line is missing a speaker, assume it's the user's first message
        if not re.match(r"^(You|ChatGPT|Claude|Gemini|Grok|Bard|AI|Assistant)\s+said:", first_line, re.IGNORECASE):
            messages.append(ChatMessage(role="user", content=first_line))
            content = "\n".join(lines[1:]) 
    
        # Re-run regex after handling first-line input
        matches = re.findall(pattern, content, re.DOTALL)
        
        for speaker, text in matches:
            # Normalize roles
            role = "user" if speaker.lower() == "you" else "assistant"
            messages.append(ChatMessage(
                role=role,
                content=text.strip()
            ))
        
        return messages if messages else self._parse_generic_format(content)
    
    def _parse_openai_web_format(self, content: str) -> List[ChatMessage]:
        """
        Parse OpenAI web export format with markdown-like sections
        """
        messages = []
        
        # Split by markdown headers
        pattern = r"#\s+(\w+)\s*\n+([\s\S]*?)(?=#\s+\w+|$)"
        matches = re.findall(pattern, content)
        
        for section, text in matches:
            # Map section names to roles
            if section.lower() in ["user", "human", "you"]:
                role = "user"
            elif section.lower() in ["assistant", "chatgpt", "gpt", "claude", "gemini", "ai"]:
                role = "assistant"
            elif section.lower() in ["system"]:
                role = "system"
            else:
                role = "unknown"
            
            messages.append(ChatMessage(
                role=role,
                content=text.strip()
            ))
        
        return messages if messages else self._parse_generic_format(content)
    
    
    def _parse_generic_format(self, content: str) -> List[ChatMessage]:
        """
        Enhanced parser with advanced heuristics to infer user vs assistant roles.
        """
        lines = content.split('\n')
        messages = []
        current_role = None
        current_content = []

        # AI stylistic patterns
        ai_patterns = [
            r"^I'm (sorry|afraid|happy to)",
            r"^As (an|a) (AI|assistant|language model)",
            r"^Let me (explain|show|help)",
            r"^Here('s| is) (how|what|why|an example)",
            r"^Certainly!", r"^Of course!", r"^Sure thing!", 
            r"^The best way to", r"^Let's go step by step", 
            r"^Based on (my knowledge|your request|the data)", 
            r"^To summarize", r"^Thank you for your question"
        ]

        # User patterns (commands, questions)
        user_patterns = [
            r"\?$",  # Ends with question mark
            r"^(Can|Could|How|What|Why|When|Where|Is|Are|Do|Does|Will|Would|Should) ",
            r"^Please ", r"^Tell me ", r"^I (need|want|would like|am trying to)",
            r"^(Write|Create|Generate|Explain|Summarize|Analyze)", 
            r"^(Claude|ChatGPT|Gemini|Assistant|AI),"
        ]

        # Code block / structured content detection
        structured_patterns = [
            r"```",  # Code block
            r"\{.*?\}",  # JSON structure
            r"def [a-zA-Z_]\w*\(.*\):",  # Python function definition
            r"^\d+\.",  # Numbered list
            r"^- ",  # Bullet points
            r"\\begin\{.*?\}"  # LaTeX
        ]

        ai_pattern = re.compile("|".join(ai_patterns), re.IGNORECASE)
        user_pattern = re.compile("|".join(user_patterns), re.IGNORECASE)
        structured_pattern = re.compile("|".join(structured_patterns))

        def detect_role_change(line):
            """
            Determines if a role change has occurred based on AI/user patterns.
            """
            # Explicit labels (best-case scenario)
            if re.match(r"^(User|Human|Me|I)[\s:]+", line, re.IGNORECASE):
                return "user"
            if re.match(r"^(AI|Assistant|Bot|ChatGPT|Claude|Gemini)[\s:]+", line, re.IGNORECASE):
                return "assistant"

            # AI-style message detection
            if ai_pattern.search(line):
                return "assistant"
        
            # User-style message detection
            if user_pattern.search(line):
                return "user"

            return None  # No strong signal

        # Process each line
        i = 0
        while i < len(lines):
            line = lines[i].strip()
        
            if not line:
                # Detect multi-line breaks (possible role change)
                empty_count = sum(1 for j in range(i+1, min(i+4, len(lines))) if not lines[j].strip())
                if empty_count >= 2 and current_content:
                    messages.append(ChatMessage(role=current_role, content='\n'.join(current_content).strip()))
                    current_content = []
                    current_role = "assistant" if current_role == "user" else "user"
                i += 1
                continue
        
            # Role detection
            detected_role = detect_role_change(line)
        
            if detected_role:
                # Save previous message
                if current_role and current_content:
                    messages.append(ChatMessage(role=current_role, content='\n'.join(current_content).strip()))
                    current_content = []

                current_role = detected_role
            
                # Remove explicit prefixes
                role_prefix_match = re.match(r"^(User|Human|Me|I|AI|Assistant|Bot|ChatGPT|Claude|Gemini)[\s:]+(.*)$", line, re.IGNORECASE)
                if role_prefix_match:
                    line = role_prefix_match.group(2).strip()

            # Infer role based on message content
            if current_role is None:
                current_role = "user"  # Assume user starts

            # Store line
            current_content.append(line)
            i += 1

        # Store last message
        if current_role and current_content:
            messages.append(ChatMessage(role=current_role, content='\n'.join(current_content).strip()))

        # Validate message order
        if len(messages) >= 2:
            for i in range(1, len(messages)):
                if messages[i].role == messages[i-1].role:
                    # If two same-role messages appear, switch the second one
                    messages[i].role = "assistant" if messages[i].role == "user" else "user"

        # Ensure at least one message
        if not messages:
            messages.append(ChatMessage(role="user", content=content.strip()))

        return messages
    