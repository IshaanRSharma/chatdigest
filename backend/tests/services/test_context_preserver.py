# import unittest
# from src.services.context_preserver import ContextPreserver
# from src.models.chat import ChatMessage
# from src.services.token_counter import estimate_tokens
# from src.services.chat_parser import ChatParser
# from src.models.chat import ParsedChat
# from pathlib import Path

# class TestContextPreserver(unittest.TestCase):
#     """Unit tests for ContextPreserver"""

#     @classmethod
#     def setUpClass(cls):
#         """Setup test data before running tests"""
#         cls.context_preserver = ContextPreserver()
#         cls.target_llm = "gpt-4"
#         cls.token_limit = 4096  # Example token limit
        
#         cls.parser = ChatParser()
#         cls.current_dir = Path(__file__).parent
#         cls.test_file_path = cls.current_dir / "sample_chat.txt"

#         # Read the file content once for all tests
#         with open(cls.test_file_path, "r", encoding="utf-8") as f:
#             cls.chat_content = f.read()
            
#         cls.parsed_chat = cls.parser.parse(cls.chat_content)    
#         cls.messages = cls.parsed_chat.messages


#     def test_preserve_context_not_empty(self):
#         """Test if the preserved context output is not empty"""
#         preserved_context = self.context_preserver.preserve_context(
#             self.messages, self.token_limit, self.target_llm
#         )
#         self.assertIsInstance(preserved_context, str)
#         self.assertTrue(len(preserved_context) > 0)

#     def test_preserve_context_within_token_limit(self):
#         """Test if the preserved context respects the token limit"""
#         preserved_context = self.context_preserver.preserve_context(
#             self.messages, self.token_limit, self.target_llm
#         )
#         token_count = estimate_tokens(preserved_context, self.target_llm)
#         self.assertLessEqual(token_count, self.token_limit)

#     def test_essential_messages_selection(self):
#         """Test if essential messages are selected correctly"""
#         selected_messages = self.context_preserver.select_essential_messages(
#             self.messages, self.token_limit
#         )
#         self.assertIsInstance(selected_messages, list)
#         self.assertGreater(len(selected_messages), 0)
#         self.assertTrue(all(isinstance(msg, ChatMessage) for msg in selected_messages))


# if __name__ == "__main__":
#     unittest.main()
