# probably need langchain chunking here -> context_preserver.py
from typing import List, Dict, Any
from src.models.chat import ChatMessage
from src.utils.helpers import extract_code_blocks, format_for_llm
from src.services.token_counter import estimate_tokens
class ContextPreserver:
    """Service that preserves essential context from chat logs"""

    def preserve_context(
        self, 
        messages: List[ChatMessage],
        token_limit: int,
        target_llm: str
    ) -> str:
        """
        Select and preserve critical messages to fit within token limits

        Strategy:
        1. Always keep first and recent messages
        2. Preserve all code blocks
        3. Select messages with high information density
        4. Format appropriately for target LLM
        """
        # Extract all code blocks
        code_blocks = []
        for msg in messages:
            blocks = extract_code_blocks(msg.content)
            code_blocks.extend(blocks)

        # Calculate tokens used by code
        code_tokens = sum(estimate_tokens(code, target_llm) for code in code_blocks)

        # Token budget for regular messages
        message_token_budget = token_limit - code_tokens - 200  # Reserve tokens for formatting

        # Message selection strategy
        preserved_messages = self.select_essential_messages(messages, message_token_budget)

        # Format messages
        formatted_lines = []
        for msg in preserved_messages:
            role_str = "Me: " if msg.role == "user" else "System response: " if msg.role == "assistant" else "System response: "
            formatted_lines.append(f"{role_str}{msg.content}")

        # Add code blocks
        content = "\n\n".join(formatted_lines)
        if code_blocks:
            content += "\n\nCode blocks:\n" + "\n\n".join(code_blocks)

        # Format as prompt for target LLM
        prompt = self.create_summary_prompt(content, content[0], code_blocks, target_llm)
        
        return prompt

    def select_essential_messages(self, messages: List[ChatMessage], token_budget: int) -> List[ChatMessage]:
        """Smart selection of messages to fit token budget"""
        # Simple algorithm:
        # 1. Always keep first message (often has instructions)
        # 2. Always keep last 3 messages (recent context)
        # 3. For middle messages, select those with high information density or key concepts

        if len(messages) <= 10:
            return messages  # Keep all if small enough

        # Always keep first and last 3
        essential_messages = [messages[0]] + messages[-3:]

        # If we have budget for more, select from middle
        if len(messages) > 10:
            middle_messages = messages[1:-3]
            # TODO: Add more sophisticated selection here
            # For now, we'll pick evenly distributed messages
            if len(middle_messages) > 0:
                step = max(1, len(middle_messages) // min(5, token_budget // 100))
                for i in range(0, len(middle_messages), step):
                    if i < len(middle_messages):
                        essential_messages.append(middle_messages[i])

        # Sort by original order
        return sorted(essential_messages, key=lambda msg: messages.index(msg))

    def compress_with_llama(self, messages: List[ChatMessage], ollama_service) -> str:
        """
        Use Llama to create a compressed representation of the conversation
        that balances comprehensiveness with technical precision
        """
        # Format the conversation for compression
        formatted_content = []
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            formatted_content.append(f"{role}: {msg.content}")
        content = "\n\n".join(formatted_content)
    
        # Create a balanced compression prompt
        prompt = """You are creating a comprehensive summary of a conversation that will be used to continue the discussion effectively.
Your task is to create a condensed yet complete summary that:

1. Preserves the core context and flow of the conversation while reducing length
   - Maintain the primary topics, questions, and key insights
   - Capture the evolution of ideas throughout the discussion

2. Prioritizes important information based on the conversation type:
   - If technical: preserve all technical details, code snippets, implementation plans
   - If conceptual: preserve key concepts, definitions, and relationships
   - If decision-making: preserve options considered, criteria, and conclusions reached

3. Always retain with high fidelity:
   - Specific facts, figures, and named references
   - Questions asked and their answers
   - Any code, formulas, or structured information
   - Explicit decisions or agreements made
   - Core requirements or constraints mentioned

4. Maintain chronological development while eliminating redundancy
   - Show how ideas progressed without repeating similar content
   - Connect related points across different parts of the conversation

The summary should contain enough detail that someone could continue the conversation with full context, without needing to reference the original discussion.

Here is the conversation to summarize:
"""
        prompt += content
        prompt += """

Create a comprehensive and balanced summary that preserves all essential context needed to continue this conversation:
"""
    
    # Use Llama to generate the compression with optimized parameters
        compressed = ollama_service.generate(prompt)
        return compressed

        
    def create_summary_prompt(self, compressed_history, recent_messages, code_blocks, target_llm):
        """
        Format a complete prompt using compressed history and recent messages
        """
        sections = []
    
        # Add compressed history
        sections.append("# Previous Conversation Summary")
        sections.append(compressed_history)
    
        # Add recent messages verbatim
        sections.append("# Recent Messages (Verbatim)")
        for msg in recent_messages:
            role_str = "User: " if msg.role == "user" else "Assistant: "
            sections.append(f"{role_str}{msg.content}")
    
        # Add code blocks if any
        if code_blocks:
            sections.append("# Code and Technical Content")
            sections.append("\n".join(code_blocks))
    
        # Create instruction for continuing
        instruction = """Based on the conversation history summarized above, please continue the discussion naturally. The most recent messages are provided verbatim to give you the exact current context."""
    
        # Combine all sections
        content = "\n\n".join(sections)
    
        return f"{instruction}\n\n{content}\n\n"