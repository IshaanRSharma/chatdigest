"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';

interface LLMType {
  id: string;
  name: string;
  token_limit: number;
}

interface Metrics {
  originalTokens: number;
  compressedTokens: number;
  reduction: number;
}

export default function Home() {
  const [chatInput, setChatInput] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [targetLLM, setTargetLLM] = useState<string>('gpt-4');
  const [llmTypes, setLLMTypes] = useState<LLMType[]>([]);
  const [summary, setSummary] = useState<string>('');
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);


  // Fetch LLM types on component mount
  useEffect(() => {
    async function fetchLLMTypes() {
      try {
        const response = await axios.get('http://localhost:8000/api/llm-types');
        setLLMTypes(response.data.llm_types);
        setTargetLLM(response.data.llm_types[0].id);
      } catch (error) {
        console.error('Error fetching LLM types:', error);
        setError('Failed to load LLM types. Please check if the backend server is running.');
      }
    }
    fetchLLMTypes();
    
    // Clean up any object URLs when component unmounts
    return () => {
      if (downloadUrl) {
        URL.revokeObjectURL(downloadUrl);
      }
    };
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      // Clear any previous error message
      setError('');
    }
  };

  const handleUploadFile = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setIsLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setChatInput(response.data.content);
      // Clear any previous summary on successful upload
      setSummary('');
      setMetrics(null);
    } catch (error: any) {
      console.error('Upload error:', error);
      setError(error.response?.data?.detail || 'Error uploading file. Please check the file format.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSummarize = async () => {
    if (!chatInput.trim()) {
      setError('Please enter chat content or upload a file');
      return;
    }

    setIsLoading(true);
    setError('');
    setSummary('');
    setMetrics(null);
    
    // Revoke previous download URL if it exists
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
      setDownloadUrl(null);
    }

    try {
      const response = await axios.post('http://localhost:8000/api/compress-context', {
        chat_content: chatInput,
        target_llm: targetLLM
      });

      setSummary(response.data.compressed_content);
      setMetrics({
        originalTokens: response.data.original_tokens,
        compressedTokens: response.data.compressed_tokens,
        reduction: response.data.reduction_percentage
      });
      
      // Create download URL for the summary
      createDownloadUrl(response.data.compressed_content);
    } catch (error: any) {
      console.error('Summarization error:', error);
      setError(error.response?.data?.detail || 'Error generating summary. Please try again or check the input format.');
    } finally {
      setIsLoading(false);
    }
  };

  const createDownloadUrl = (content: string) => {
    // Create a Blob with the text content
    const blob = new Blob([content], { type: 'text/plain' });
    
    // Create and store the URL
    const url = URL.createObjectURL(blob);
    setDownloadUrl(url);
  };

  const downloadSummary = () => {
    if (!summary) {
      setError('No summary available to download');
      return;
    }

    // If we don't have a download URL yet, create one
    if (!downloadUrl) {
      createDownloadUrl(summary);
    }

    // Create a temporary anchor element and trigger download
    const element = document.createElement('a');
    element.href = downloadUrl as string;
    
    // Generate filename with date and LLM type
    const date = new Date().toISOString().split('T')[0];
    const filename = `chat-summary-${targetLLM}-${date}.txt`;
    
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  // Handle textarea input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatInput(e.target.value);
    // Clear summary when input changes
    if (summary) {
      setSummary('');
      setMetrics(null);
      
      // Revoke previous download URL
      if (downloadUrl) {
        URL.revokeObjectURL(downloadUrl);
        setDownloadUrl(null);
      }
    }
  };

  const openSummaryModal = () => {
    setIsModalOpen(true);
  };
  

  const closeSummaryModal = () => {
    setIsModalOpen(false);
  };

  return (
    <div className="max-w-6xl mx-auto p-8 bg-[#FEFAE0]">
      <header className="flex items-center justify-between mb-8 border-b-2 border-[#2A2A2A]/30 pb-4">
        <div className="flex items-center gap-6">
          <h1 className="text-3xl font-black text-[#B35A1F] font-mono tracking-tight flex items-center">
            Chat
            <span className="text-[#2A2A2A]/80">Digest</span>
          </h1>
        </div>
        
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/yourusername/chat-digest"
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-2 px-3 py-1.5 text-sm text-[#2A2A2A]/80 hover:text-[#2A2A2A] transition-colors duration-200"
          >
            <svg
              className="w-5 h-5"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span className="font-medium">GitHub</span>

          </a>
        </div>
      </header>

      <div className="mb-12 text-center">
        <h2 className="text-lg font-mono font-bold text-[#2A2A2A]/80 max-w-3xl mx-auto leading-relaxed">
          Preserve context of your chat logs when transferring between different LLMs or LLM instances.
        </h2>
      </div>

      <main className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-[#E9EDC9] rounded-lg p-6 shadow border border-[#CCD5AE]">
          <h2 className="text-3xl font-bold mb-4 text-[#B35A1F]">Input</h2>
          
          <div className="flex items-center mb-4">
            <div className="relative">
              <input 
                type="file" 
                onChange={handleFileChange} 
                accept=".txt,.json,.md" 
                disabled={isLoading}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
              <div className="px-4 py-2 bg-[#FEFAE0] text-[#5c4935] border-2 border-[#CCD5AE] rounded-lg
                shadow-[2px_2px_0px_#D4A373] hover:shadow-[1px_1px_0px_#D4A373] 
                active:shadow-[0px_0px_0px_#D4A373] active:translate-x-[2px] active:translate-y-[2px]
                transition-all duration-150 cursor-pointer">
                Choose File
              </div>
            </div>
            <button 
              onClick={handleUploadFile} 
              disabled={!file || isLoading}
              className="ml-4 px-4 py-2 bg-[#FEFAE0] text-[#5c4935] border-2 border-[#CCD5AE] rounded-lg
              shadow-[3px_3px_0px_#D4A373] hover:shadow-[1px_1px_0px_#D4A373] 
              active:shadow-[0px_0px_0px_#D4A373] active:translate-x-[3px] active:translate-y-[3px]
              transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed 
              disabled:shadow-none disabled:transform-none"
            >
              {isLoading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
          
          <textarea
            value={chatInput}
            onChange={handleInputChange}
            placeholder="Paste your chat log here or upload a file..."
            rows={12}
            disabled={isLoading}
            className="w-full p-3 border border-[#CCD5AE] rounded bg-[#FEFAE0] text-[#5c4935] font-mono resize-y mb-4"
          />
          
          <div className="flex items-center gap-3">
            <label className="text-[#5c4935] flex items-center gap-1.5">
              <span className="text-sm">Target LLM:</span>
              <div className="relative inline-block w-52">
                <select 
                  value={targetLLM} 
                  onChange={(e) => setTargetLLM(e.target.value)}
                  disabled={isLoading}
                  className="appearance-none px-3 py-1.5 pr-8 w-full bg-[#FEFAE0] text-[#5c4935] border-2 border-[#CCD5AE] rounded-lg
                  shadow-[2px_2px_0px_#D4A373] hover:shadow-[1px_1px_0px_#D4A373] 
                  active:shadow-[0px_0px_0px_#D4A373] active:translate-x-[2px] active:translate-y-[2px]
                  transition-all duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed
                  disabled:shadow-none disabled:transform-none focus:outline-none text-xs truncate"
                >
                  {llmTypes.map(llm => (
                    <option 
                      key={llm.id} 
                      value={llm.id}
                      className="text-xs"
                    >
                      {llm.name} ({(llm.token_limit / 1000).toFixed(0)}K)
                    </option>
                  ))}
                </select>
              </div>
            </label>
            
            <button 
              onClick={handleSummarize} 
              disabled={isLoading || !chatInput.trim()}
              className="px-4 py-1.5 bg-[#FEFAE0] text-[#5c4935] text-sm border-2 border-[#B35A1F] rounded-lg
              shadow-[3px_3px_0px_#B35A1F] hover:shadow-[1px_1px_0px_#B35A1F] 
              active:shadow-[0px_0px_0px_#B35A1F] active:translate-x-[3px] active:translate-y-[3px]
              transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed 
              disabled:shadow-none disabled:transform-none"
            >
              {isLoading ? 'Processing...' : 'Generate'}
            </button>
          </div>
          
          {error && <div className="text-[#c24e2c] mt-4">{error}</div>}
        </div>

        <div className="bg-[#E9EDC9] rounded-lg p-6 shadow border border-[#CCD5AE]">
          <h2 className="text-3xl font-bold mb-4 text-[#B35A1F]">Output</h2>
          
          {metrics && (
            <div className="flex flex-wrap gap-4 mb-4 items-center p-3 bg-[#FAEDCD] rounded border border-[#CCD5AE]">
              <div className="min-w-[150px] flex-1 text-[#5c4935]">
                Original: {metrics.originalTokens.toLocaleString()} tokens
              </div>
              <div className="min-w-[150px] flex-1 text-[#5c4935]">
                Synthesized: {metrics.compressedTokens.toLocaleString()} tokens
              </div>
              <div className="min-w-[150px] flex-1 text-[#5c4935]">
                Reduction: {metrics.reduction}%
              </div>
              
              <button 
                onClick={downloadSummary} 
                disabled={!summary}
                className="px-4 py-2 bg-[#FEFAE0] text-[#5c4935] border-2 border-[#CCD5AE] rounded-lg
                shadow-[3px_3px_0px_#CCD5AE] hover:shadow-[1px_1px_0px_#CCD5AE] 
                active:shadow-[0px_0px_0px_#CCD5AE] active:translate-x-[3px] active:translate-y-[3px]
                transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed
                disabled:shadow-none disabled:transform-none"
              >
                Download as .txt
              </button>
            </div>
          )}
          
          {summary ? (
            <div className="h-[450px] overflow-y-auto border border-[#CCD5AE] rounded relative cursor-pointer"
              onClick={openSummaryModal}
              style={{ overflowY: 'auto', overflowX: 'auto' }}
            >
              <div className="relative">
              <SyntaxHighlighter 
                language="plaintext" 
                customStyle={{ 
                  margin: 0, 
                  borderRadius: '4px',
                  backgroundColor: '#FEFAE0',
                  color: '#5c4935',
                  height: '100%',
                  fontWeight: 600,
                  fontFamily: "'Space Mono', 'JetBrains Mono', monospace",
                  letterSpacing: '0.02em',
                  lineHeight: '1.6',
                  textTransform: 'lowercase',
                  mixBlendMode: 'multiply'
                }}
              >
                {summary}
              </SyntaxHighlighter>
              </div>

              <div className="absolute inset-0 flex items-center justify-center bg-black/10 opacity-0 hover:opacity-100 transition-opacity">
                <span className="px-3 py-1.5 bg-[#FEFAE0] text-[#5c4935] rounded-lg shadow text-sm font-medium">
                  Click to expand
                </span>
              </div>
            </div>
          ) : !isLoading ? (
            <div className="h-[450px] flex items-center justify-center bg-[#FEFAE0] border border-[#CCD5AE] rounded text-[#83684a] font-semibold">
              Synthesized output will appear here
            </div>
          ) : (
            <div className="h-[450px] flex items-center justify-center bg-[#FEFAE0] border border-[#CCD5AE] rounded text-[#83684a] font-semibold">
              Processing your chat log...
            </div>
          )}
        </div>
      </main>

      <footer className="mt-8 text-center">
        <p className="text-[#B35A1F] max-w-2xl mx-auto leading-relaxed font-semibold">
          Compress your chat logs into context-preserving prompts, enabling seamless conversation continuity when switching between different LLMs or LLM instances.
        </p>
      </footer>

      {isModalOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => setIsModalOpen(false)}
        >
          <div 
            className="relative w-full max-w-4xl max-h-[90vh] bg-[#FEFAE0] p-6 rounded-lg shadow-lg overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              onClick={closeSummaryModal} 
              className="absolute top-2 right-2 p-2 text-[#5c4935] hover:text-[#B35A1F] transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            <h2 className="text-2xl font-bold mb-4 text-[#B35A1F]">Complete Output</h2>
            <div className="font-mono text-[#5c4935] whitespace-pre-wrap">
              {summary}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
