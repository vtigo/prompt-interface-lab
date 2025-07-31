'use client';

import { Button } from '@/components/ui/button';
import { useChat } from '@ai-sdk/react';
import { UIMessage } from 'ai';
import { useEffect, useState } from 'react';

export default function Chat() {
  const { messages, data, input, handleInputChange, handleSubmit, status, error } = useChat({
    api: 'http://localhost:8000/api/chat',
    streamProtocol: 'data',
    onError: (error) => {
      console.error('Chat error:', error);
    },
  });

  const [messageFiles, setMessageFiles] = useState<Record<string, any[]>>({});

  const [showInfo, setShowInfo] = useState(false)
  const isLoading = status != "ready"
  const userName = "tigo"
  const agentName = "Senno Scout"

  useEffect(() => {
    console.log(data)
    // Associate file data with the current assistant message
    if (data && data.length > 0 && messages.length > 0) {
      const lastAssistantMessage = messages.filter(m => m.role === 'assistant').slice(-1)[0];
      if (lastAssistantMessage) {
        setMessageFiles(prev => ({
          ...prev,
          [lastAssistantMessage.id]: data
        }));
      }
    }
  }, [data, messages])

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-foreground">Chat Interface</h1>
        <p className="text-sm text-foreground/70">
          Proof of concept using Vercel's useChat hook with Data Stream Protocol
        </p>
        <Button variant="ghost" onClick={() => setShowInfo(prev => !prev)}>toggle info</Button>
      </div>

      {
        showInfo && <MessagesInfos messages={messages} />}

      <div className="flex-1 overflow-y-auto border border-black/[.08] dark:border-white/[.145] rounded-lg p-4 mb-4 bg-background">
        {messages.length === 0 ? (
          <div className="text-center text-foreground/50 mt-8">
            <p>Start a conversation by typing a message below.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${message.role === 'user'
                    ? 'bg-foreground text-background'
                    : 'bg-zinc-100 dark:bg-white/[.06] text-foreground'
                    }`}
                >
                  <div className="text-xs font-medium mb-1 opacity-70">
                    {message.role === 'user' ? userName : agentName}
                  </div>
                  <div className="whitespace-pre-wrap">{message.content}</div>

                  {message.role === 'assistant' && messageFiles[message.id] && !isLoading && (
                    <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded text-xs">
                      <div className="font-medium text-blue-800 dark:text-blue-200 mb-1">File Data:</div>
                      {messageFiles[message.id].map((item: any, idx) => (
                        <div key={idx} className="mb-2">
                          <div className="font-medium text-blue-600 dark:text-blue-400">
                            📄 {item.filename} ({item.size} bytes)
                          </div>
                          <pre className="text-blue-700 dark:text-blue-300 overflow-x-auto text-xs mt-1 bg-white/50 dark:bg-white/5 p-2 rounded">
                            {item.content}
                          </pre>
                        </div>
                      ))}
                    </div>
                  )}

                </div>
              </div>
            ))}
          </div>
        )}

        {isLoading && (
          <div className="flex justify-start mt-4">
            <div className="bg-black/[.05] dark:bg-white/[.06] text-foreground rounded-lg p-3">
              <div className="text-xs font-medium mb-1 opacity-70">AI</div>
              <div className="flex items-center space-x-1">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm text-foreground/70 ml-2">AI is typing...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="text-red-800 dark:text-red-200 text-sm">
            <strong>Error:</strong> {error.message}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="Type your message here..."
          disabled={isLoading}
          className="flex-1 px-4 py-2 border border-black/[.08] dark:border-white/[.145] rounded-lg bg-background text-foreground placeholder:text-foreground/50 focus:outline-none focus:ring-2 focus:ring-foreground/20 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="px-6 py-2 bg-foreground text-background rounded-lg font-medium hover:bg-foreground/90 focus:outline-none focus:ring-2 focus:ring-foreground/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </form>

    </div>
  );
}

const MessagesInfos = ({ messages }: { messages: UIMessage[] }) => {
  return (
    <div className={"flex-1 flex flex-col overflow-y-scroll"}>
      {messages.map(message => (
        <div className='whitespace-nowrap'>
          <span>{message.id} - </span>
          <span>{message.role}: </span>

        </div>
      ))}
    </div>
  )
}
