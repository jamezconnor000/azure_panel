/**
 * Aether Familiar Chat Widget
 * Embedded AI development assistant for Aether Saga
 */

import React, { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface FamiliarChatProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FamiliarChat: React.FC<FamiliarChatProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'system',
      content: 'Aether Familiar ready. How can I help you develop?',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // WebSocket connection
  useEffect(() => {
    if (!isOpen) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8080/ws/familiar`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'connected') {
        setIsConnected(true);
      } else if (data.type === 'chunk') {
        // Append to last assistant message
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant') {
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + data.content },
            ];
          }
          return prev;
        });
      } else if (data.type === 'thinking') {
        // Add placeholder for assistant response
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: '',
            timestamp: new Date(),
          },
        ]);
      } else if (data.type === 'done') {
        setIsLoading(false);
      } else if (data.type === 'error') {
        setIsLoading(false);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'system',
            content: `Error: ${data.message}`,
            timestamp: new Date(),
          },
        ]);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [isOpen]);

  const sendMessage = () => {
    if (!input.trim() || isLoading || !wsRef.current) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    wsRef.current.send(
      JSON.stringify({
        type: 'chat',
        message: userMessage.content,
      })
    );
  };

  const clearHistory = () => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'clear' }));
    }
    setMessages([
      {
        id: '0',
        role: 'system',
        content: 'Conversation cleared. How can I help?',
        timestamp: new Date(),
      },
    ]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-4 right-4 w-96 h-[600px] bg-gray-900 rounded-lg shadow-2xl border border-cyan-500/30 flex flex-col z-50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800 rounded-t-lg">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-cyan-400 font-semibold">Aether Familiar</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearHistory}
            className="text-gray-400 hover:text-white text-sm"
            title="Clear history"
          >
            Clear
          </button>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
            title="Close"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-cyan-600 text-white'
                  : msg.role === 'system'
                  ? 'bg-gray-700 text-gray-300 text-sm italic'
                  : 'bg-gray-800 text-gray-100'
              }`}
            >
              <pre className="whitespace-pre-wrap font-sans text-sm">
                {msg.content || (isLoading ? '...' : '')}
              </pre>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-700 bg-gray-800 rounded-b-lg">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isConnected ? 'Ask Familiar...' : 'Connecting...'}
            disabled={!isConnected || isLoading}
            className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:opacity-50"
            rows={2}
          />
          <button
            onClick={sendMessage}
            disabled={!isConnected || isLoading || !input.trim()}
            className="bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 transition-colors"
          >
            {isLoading ? (
              <svg
                className="w-5 h-5 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
            ) : (
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Floating button to open Familiar chat
 */
export const FamiliarButton: React.FC<{ onClick: () => void }> = ({
  onClick,
}) => {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-4 right-4 w-14 h-14 bg-cyan-600 hover:bg-cyan-500 rounded-full shadow-lg flex items-center justify-center text-white transition-all hover:scale-110 z-40"
      title="Open Aether Familiar"
    >
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
        />
      </svg>
    </button>
  );
};

export default FamiliarChat;
