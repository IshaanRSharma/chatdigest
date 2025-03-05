import unittest
from pathlib import Path
from src.services.chat_parser import ChatParser
from src.models.chat import ParsedChat

class TestChatParser(unittest.TestCase):
    """Unit tests for ChatParser"""

    @classmethod
    def setUpClass(cls):
        """Setup before running tests"""
        cls.parser = ChatParser()
        cls.current_dir = Path(__file__).parent
        cls.test_file_path = cls.current_dir / "sample_chat.txt"

        # Read the file content once for all tests
        with open(cls.test_file_path, "r", encoding="utf-8") as f:
            cls.chat_content = f.read()

    def test_parser_output_not_empty(self):
        """Test if parsed chat is not None or empty"""
        parsed_chat: ParsedChat = self.parser.parse(self.chat_content)
        self.assertIsNotNone(parsed_chat)
        print("=== Parsed Chat ===")
        for message in parsed_chat.messages:
            print(f"[{message.role}] {message.content}")        
        self.assertTrue(parsed_chat.messages)  # Ensure messages exist

    def test_detected_format_exists(self):
        """Test if the detected chat format is returned"""
        parsed_chat: ParsedChat = self.parser.parse(self.chat_content)
        print("\n=== Detected Format ===")
        print(parsed_chat.format_detected)
        self.assertIsNotNone(parsed_chat.format_detected)

    def test_token_count_valid(self):
        """Test if token count is a valid number"""
        parsed_chat: ParsedChat = self.parser.parse(self.chat_content)
        self.assertIsInstance(parsed_chat.token_count, int)
        print("\n=== Token Count ===")
        print(parsed_chat.token_count)
        self.assertGreaterEqual(parsed_chat.token_count, 0)

    def test_message_count_valid(self):
        """Test if message count is a valid number"""
        parsed_chat: ParsedChat = self.parser.parse(self.chat_content)
        self.assertIsInstance(parsed_chat.message_count, int)
        print("\n=== Message Count ===")
        print(parsed_chat.message_count)
        self.assertGreaterEqual(parsed_chat.message_count, 0)

if __name__ == "__main__":
    unittest.main()
