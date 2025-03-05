 PYTHONPATH=$(pwd) python -m unittest discover tests
 PYTHONPATH=$(pwd) python -m unittest tests.services.test_context_preserver
PYTHONPATH=$(pwd) python -m unittest tests.services.test_chat_parser