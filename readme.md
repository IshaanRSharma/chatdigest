# ChatDigest 🔥
**Transform massive chat logs into context-preserving prompts that seamlessly bridge conversations across different LLMs.**
Ever lost the thread when switching between ChatGPT, Claude, or other AI assistants? ChatDigest intelligently compresses your conversation history while preserving all the crucial context, technical details, and code blocks that matter. Perfect for developers, researchers, and power users who work across multiple AI platforms.

---

## 🚀 Quick Start
### Prerequisites
- Python 3.8+
- Node.js 18+
- Ollama (for local LLM processing)

### Backend Setup
1. **Clone and navigate to backend**
   cd chatdigest/backend
2. **Create virtual environment**
     python -m venv venv
     source venv/bin/activate
3. **Install dependencies**
   pip install -r requirements.txt
4. **Start the FastAPI server**
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

### Frontend Setup
1. **Navigate to frontend**
   cd chatdigest/frontend
2. **Install dependencies**
   npm install
3. **Start the development server**
   npm run dev
4. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 🎯 How It Works
1. **Upload or paste** your chat log from any LLM platform
2. **Select your target LLM** and token limits
3. **Generate** a compressed summary that preserves:
   - Technical details and code blocks
   - Key decisions and requirements
   - Conversation flow and context
   - Questions and their answers

4. **Copy the output** and continue your conversation seamlessly on any platform
