'use client';

import { useState, FormEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          chat_history: messages.map(msg => ({
            human: msg.role === 'user' ? msg.content : null,
            ai: msg.role === 'assistant' ? msg.content : null,
          })).filter(msg => msg.human !== null || msg.ai !== null),
        }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Add assistant's response
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
        },
      ]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, there was an error processing your request.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-white dark:bg-gray-900">
      <div className="container mx-auto px-4">
        <header className="py-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            What the Gov
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Ask questions about U.S. Executive Orders
          </p>
        </header>
        <div className="max-w-5xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="flex flex-col h-[800px]">
            <div className="flex-1 overflow-y-auto mb-4 space-y-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 dark:text-gray-400">
                  Start a conversation by asking about U.S. Executive Orders
                </div>
              ) : (
                <div className="flex flex-col gap-6 p-4">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`p-6 rounded-lg ${
                        message.role === "user"
                          ? "bg-blue-500 text-white self-end max-w-[80%]"
                          : "bg-gray-800 text-white max-w-[90%]"
                      }`}
                    >
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        className="prose prose-invert max-w-none"
                        components={{
                          // Override paragraph to preserve whitespace
                          p: ({node, ...props}) => (
                            <p className="whitespace-pre-wrap mb-4 last:mb-0" {...props} />
                          ),
                          // Style headings
                          h1: ({node, ...props}) => (
                            <h1 className="text-2xl font-bold mb-4" {...props} />
                          ),
                          h2: ({node, ...props}) => (
                            <h2 className="text-xl font-bold mb-3" {...props} />
                          ),
                          h3: ({node, ...props}) => (
                            <h3 className="text-lg font-bold mb-2" {...props} />
                          ),
                          // Style lists
                          ul: ({node, ...props}) => (
                            <ul className="list-disc pl-4 mb-4 space-y-2" {...props} />
                          ),
                          ol: ({node, ...props}) => (
                            <ol className="list-decimal pl-4 mb-4 space-y-2" {...props} />
                          ),
                          li: ({node, ordered, ...props}) => (
                            <li className="mb-2 pl-2" {...props} />
                          ),
                          // Style code blocks
                          code: ({node, inline, ...props}) => (
                            inline 
                              ? <code className="bg-gray-700 px-1 rounded" {...props} />
                              : <code className="block bg-gray-700 p-4 rounded mb-4" {...props} />
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="border-t pt-4">
              <form onSubmit={handleSubmit} className="flex gap-4">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about U.S. Executive Orders..."
                  className="flex-1 p-4 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className={`px-6 py-4 bg-blue-500 text-white rounded-lg transition-colors ${
                    isLoading
                      ? 'opacity-50 cursor-not-allowed'
                      : 'hover:bg-blue-600'
                  }`}
                >
                  {isLoading ? 'Sending...' : 'Send'}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
