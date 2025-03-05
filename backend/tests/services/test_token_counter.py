import unittest
from src.services.token_counter import estimate_tokens, get_token_limit

class TestTokenCounter(unittest.TestCase):

    def test_estimate_tokens(self):
        text = "COunt these mf tokens"
        model = "gpt-4o"
        token_count = estimate_tokens(text, model)
        print(token_count)
        self.assertIsInstance(token_count, int)
        self.assertGreater(token_count, 0)

    def test_get_token_limit(self):
        model = "gpt-3.5-turbo"
        token_limit = get_token_limit(model)
        self.assertIsInstance(token_limit, int)
        self.assertGreater(token_limit, 0)

if __name__ == "__main__":
    unittest.main()
