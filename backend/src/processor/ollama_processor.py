# src/services/ollama_processor.py
import concurrent.futures
import re
from typing import List, Dict, Any, Optional, Tuple
from src.models.chat import ChatMessage

class OllamaProcessor:
    """Service for processing conversations using Ollama with context-preserving map-reduce summarization"""
    
    def __init__(self, ollama_service):
        self.ollama_service = ollama_service
    
    def process_conversation(
        self, 
        messages: List[ChatMessage],
        max_tokens: int = 4000,
        max_workers: int = 3,
        preserve_recent: int = 3
    ) -> Tuple[str, List[ChatMessage]]:
        """
        Process a conversation using context-preserving hierarchical map-reduce
        
        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens in the summary
            max_workers: Maximum parallel workers
            preserve_recent: Number of recent messages to preserve verbatim
            
        Returns:
            Tuple[str, List[ChatMessage]]: Compressed history and recent messages
        """
        if len(messages) <= preserve_recent:
            return "", messages
        
        # Split into historical and recent messages
        split_index = max(len(messages) - preserve_recent, 1)
        historical = messages[:split_index]
        recent = messages[split_index:]
        
        # Extract code blocks to preserve them
        code_blocks = self._extract_code_blocks(historical)
        
        # Handle small conversations directly (no chunking)
        if len(historical) <= 12:
            summarized = self._format_and_summarize(historical)
        else:
            # Create overlapping chunks and process with hierarchical map-reduce
            summarized = self._hierarchical_summarize(historical, max_tokens, max_workers)
        
        # Ensure code blocks are preserved
        summarized = self._ensure_code_blocks_present(summarized, code_blocks)
        
        return summarized, recent
    
    def _hierarchical_summarize(
        self, 
        messages: List[ChatMessage], 
        max_tokens: int,
        max_workers: int
    ) -> str:
        """Process messages using hierarchical summarization with overlapping chunks"""
        # PHASE 1: Create overlapping chunks
        chunks, chunk_metadata = self._create_overlapping_chunks(messages)
        
        # PHASE 2: Map - Process chunks with context awareness
        chunk_summaries = self._process_chunks_with_context(chunks, chunk_metadata, max_workers)
        
        # If we have few summaries, combine them directly
        if len(chunk_summaries) <= 3:
            return self._combine_summaries(chunk_summaries, is_final=True)
        
        # PHASE 3: Intermediate reduce - Group summaries and combine
        grouped_summaries = [chunk_summaries[i:i+3] for i in range(0, len(chunk_summaries), 3)]
        intermediate_summaries = []
        
        for group in grouped_summaries:
            intermediate = self._combine_summaries(group, is_final=False)
            intermediate_summaries.append(intermediate)
        
        # PHASE 4: Final reduce - Combine intermediate summaries
        return self._combine_summaries(intermediate_summaries, is_final=True)
    
    def _create_overlapping_chunks(
        self, 
        messages: List[ChatMessage], 
        chunk_size: int = 8, 
        overlap: int = 2
    ) -> Tuple[List[List[ChatMessage]], List[Dict[str, Any]]]:
        """Create overlapping chunks to preserve cross-chunk context"""
        if len(messages) <= chunk_size:
            return [messages], [{"index": 0, "total": 1, "is_first": True, "is_last": True}]
            
        chunks = []
        metadata = []
        
        for i in range(0, len(messages), chunk_size - overlap):
            # Don't go beyond array bounds
            end_idx = min(i + chunk_size, len(messages))
            
            # For very small final chunks, merge with previous
            if end_idx - i < chunk_size // 2 and chunks:
                chunks[-1].extend(messages[i:end_idx])
                metadata[-1]["is_last"] = True
            else:
                chunks.append(messages[i:end_idx])
                metadata.append({
                    "index": len(chunks) - 1,
                    "total": (len(messages) - 1) // (chunk_size - overlap) + 1,
                    "is_first": i == 0,
                    "is_last": end_idx == len(messages)
                })
        
        return chunks, metadata
    
    def _process_chunks_with_context(
        self, 
        chunks: List[List[ChatMessage]],
        metadata: List[Dict[str, Any]],
        max_workers: int
    ) -> List[str]:
        """Process chunks with awareness of chunk position and neighbors"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            for i, (chunk, meta) in enumerate(zip(chunks, metadata)):
                # Create context description
                context_desc = self._create_context_description(i, chunks, meta)
                
                # Submit task with context
                futures.append(executor.submit(
                    self._format_and_summarize_with_context, 
                    chunk,
                    context_desc,
                    meta
                ))
            
            # Collect results while maintaining order
            results = [None] * len(chunks)
            for future in concurrent.futures.as_completed(futures):
                idx = futures.index(future)
                try:
                    results[idx] = future.result()
                except Exception as e:
                    print(f"Error processing chunk {idx}: {e}")
                    # Fallback to basic formatting if summarization fails
                    results[idx] = f"[Summary failed for segment {idx+1}]\n\n" + self._format_messages(chunks[idx])
            
            return [r for r in results if r is not None]
    
    def _create_context_description(
        self, 
        chunk_idx: int, 
        chunks: List[List[ChatMessage]], 
        meta: Dict[str, Any]
    ) -> str:
        """Create a description of the context for a chunk"""
        context = f"This is part {meta['index']+1} of {meta['total']} of the conversation. "
        
        if meta["is_first"]:
            context += "This is the beginning of the conversation. "
        else:
            # Add brief context from end of previous chunk
            prev_chunk = chunks[chunk_idx - 1]
            if prev_chunk:
                last_msg = prev_chunk[-1]
                context += f"It follows a message where the {last_msg.role} was discussing: "
                # Extract topic from last message (first 50 chars)
                topic = last_msg.content[:50] + "..." if len(last_msg.content) > 50 else last_msg.content
                context += f"'{topic}'. "
        
        if meta["is_last"]:
            context += "This is the end of the conversation being summarized."
        else:
            # Add brief context about start of next chunk
            next_chunk = chunks[chunk_idx + 1]
            if next_chunk:
                first_msg = next_chunk[0]
                context += f"It is followed by a message where the {first_msg.role} begins discussing: "
                # Extract topic from first message of next chunk
                topic = first_msg.content[:50] + "..." if len(first_msg.content) > 50 else first_msg.content
                context += f"'{topic}'."
        
        return context
    
    def _format_and_summarize_with_context(
        self, 
        messages: List[ChatMessage],
        context_desc: str,
        meta: Dict[str, Any]
    ) -> str:
        """Format messages with context and generate a summary"""
        # Format the messages
        formatted_text = self._format_messages(messages)
        
        # Create summarization prompt with context awareness
        prompt = f"""Summarize this conversation segment concisely while preserving all important information.

CONTEXT: {context_desc}

You MUST preserve:
1. All questions and their answers
2. All technical details and implementation information
3. All code snippets and code references
4. Important decisions and requirements mentioned
5. References to earlier or later parts of the conversation
6. The flow and continuity of technical discussions

{"As this is the beginning of the conversation, include all context-setting information." if meta["is_first"] else ""}
{"As this is the end of the historical conversation, ensure you provide a proper lead-in to subsequent messages." if meta["is_last"] else ""}

Focus on factual technical information rather than conversational elements.

Conversation segment:
"""
        prompt += formatted_text
        prompt += "\n\nConcise summary preserving all key information:"
        
        # Call Ollama
        try:
            return self.ollama_service.generate(prompt, {
                "temperature": 0.1,
                "num_predict": 2048,
                "top_p": 0.8
            })
        except Exception as e:
            print(f"Summarization error: {e}")
            # Return formatted text with error note
            return f"[Summarization failed: {str(e)}]\n\n{formatted_text[:500]}..."
    
    def _combine_summaries(self, summaries: List[str], is_final: bool = False) -> str:
        """Combine multiple summaries with awareness of their relationships"""
        # Join summaries with clear separators
        combined_content = "\n\n---\n\n".join(summaries)
        
        # Create prompt for combining summaries
        prompt = f"""{"Create the final comprehensive summary" if is_final else "Create an intermediate summary"} from these conversation segment summaries.

Your task is to create a {"complete, cohesive summary" if is_final else "partial summary"} that:
1. Preserves ALL technical details from every section
2. Keeps ALL code snippets intact exactly as written
3. Maintains the chronological flow and narrative continuity
4. Creates smooth transitions between topics
5. Eliminates redundancy while preserving unique information
6. {"Provides a complete picture of the entire conversation" if is_final else "Prepares for further summarization"}

{"The summary should be detailed enough to continue the conversation without the original content." if is_final else ""}

Segment summaries to combine:
"""
        prompt += combined_content
        prompt += "\n\nCombined summary preserving all essential information:"
        
        # Token limit based on whether this is final
        token_limit = 3072 if is_final else 2048
        
        try:
            return self.ollama_service.generate(prompt, {
                "temperature": 0.1,
                "num_predict": token_limit,
                "top_p": 0.8
            })
        except Exception as e:
            print(f"Combination error: {e}")
            # Return concatenated summaries with error note
            return f"[Combination failed: {str(e)}]\n\n{combined_content[:1000]}..."
    
    def _extract_code_blocks(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """Extract code blocks with language information"""
        code_blocks = []
        # Pattern to match code blocks with or without language specification
        code_pattern = r"```([\w]*)\n(.*?)```"
        
        for msg in messages:
            content = msg.content
            matches = re.findall(code_pattern, content, re.DOTALL)
            
            for lang, block in matches:
                if block.strip():
                    code_blocks.append({
                        "language": lang.strip() if lang.strip() else "text",
                        "code": block.strip()
                    })
                    
            # Also check for inline code that might contain important snippets
            if '`' in content:
                inline_pattern = r"`([^`\n]{3,}?)`"
                inline_matches = re.findall(inline_pattern, content)
                
                for match in inline_matches:
                    # Only include if it looks like code (has programming syntax)
                    if re.search(r"[=(){}\[\]<>]|\w+\(", match) and match.strip():
                        code_blocks.append({
                            "language": "text",
                            "code": match.strip()
                        })
        
        return code_blocks
    
    def _ensure_code_blocks_present(self, summary: str, code_blocks: List[Dict[str, str]]) -> str:
        """Ensure all code blocks are present in the summary"""
        if not code_blocks:
            return summary
            
        # Check which code blocks are missing
        missing_blocks = []
        
        for block in code_blocks:
            code = block["code"]
            # Skip very short code blocks
            if len(code) < 20:
                continue
                
            # Create normalized versions for comparison
            simple_code = re.sub(r'\s+', ' ', code).strip()
            simple_summary = re.sub(r'\s+', ' ', summary).strip()
            
            # Check if code block is substantially present in summary
            if simple_code not in simple_summary:
                # For longer code blocks, check key parts (first line, last line)
                code_lines = code.split('\n')
                if len(code_lines) > 2:
                    first_line = code_lines[0].strip()
                    last_line = code_lines[-1].strip()
                    
                    # If both first and last lines are missing, consider the block missing
                    if first_line and last_line and first_line not in summary and last_line not in summary:
                        missing_blocks.append(block)
                else:
                    missing_blocks.append(block)
        
        # Add missing code blocks if any
        if missing_blocks:
            summary += "\n\n## Important Code Blocks\n\n"
            summary += "The following code snippets from the conversation must be preserved:\n\n"
            
            for block in missing_blocks:
                lang = block["language"]
                code = block["code"]
                
                # Use language specification if available
                if lang and lang != "text":
                    summary += f"```{lang}\n{code}\n```\n\n"
                else:
                    summary += f"```\n{code}\n```\n\n"
        
        return summary
    
    def _format_messages(self, messages: List[ChatMessage]) -> str:
        """Format messages for processing"""
        formatted = []
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        
        return "\n\n".join(formatted)
    
    def create_summary_prompt(
        self, 
        summarized_history: str, 
        recent_messages: List[ChatMessage], 
        code_blocks: List, 
        target_llm: str
    ) -> str:
        """
        Format a complete prompt for continuation using summarized history and recent messages
        
        Args:
            summarized_history: Summarized conversation history
            recent_messages: Recent messages to include verbatim
            code_blocks: Code blocks (will be handled by _ensure_code_blocks_present)
            target_llm: Target LLM for appropriate formatting
            
        Returns:
            str: Formatted prompt for continuing the conversation
        """
        sections = []
        
        # Add summarized history with a clear header
        sections.append("# Previous Conversation Summary")
        sections.append(summarized_history)
        
        # Add recent messages verbatim with a clear header
        if recent_messages:
            sections.append("# Recent Messages (Verbatim)")
            for msg in recent_messages:
                role_str = "User: " if msg.role == "user" else "Assistant: "
                sections.append(f"{role_str}{msg.content}")
        
        # Create instruction for continuing
        instruction = "Based on the conversation history summarized above and the recent messages, please continue the discussion naturally. The most recent messages are provided verbatim to give you the exact current context."
        
        # Combine all sections
        content = "\n\n".join(sections)
        
        # Format based on target LLM
        if target_llm.startswith("gpt-"):
            return f"System: {instruction}\n\n{content}\n\nUser: "
        elif target_llm.startswith("claude-"):
            return f"Human: {instruction}\n\n{content}\n\nHuman: "
        elif target_llm.startswith("gemini-"):
            return f"User: {instruction}\n\n{content}\n\nUser: "
        else:
            return f"{instruction}\n\n{content}\n\n"