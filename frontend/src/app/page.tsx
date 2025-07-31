'use client';

import { Button } from '@/components/ui/button';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { FilePanel } from '@/components/file-panel';
import { ReasoningCogs } from '@/components/icons/reasoning-cogs';
import { ArrowRight } from 'lucide-react';
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
    onFinish: (message) => {
      console.log('Message finished:', message);
      console.log('Message parts detail:', message.parts);
      message.parts?.forEach((part, index) => {
        console.log(`Part ${index}:`, part);
      });
    },
  });

  const [messageFiles, setMessageFiles] = useState<Record<string, any[]>>({});
  const [showDebugInfo, setShowDebugInfo] = useState(false)
  const isLoading = status != "ready"

  useEffect(() => {
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
    <div className="flex flex-col bg-zinc-100 h-screen text-zinc-700">
      <div className='flex flex-col w-full max-w-4xl mx-auto h-full mt-12 p-4'>
        <div className="mb-4">
          <h1 className="text-2xl font-bold">Chat Interface</h1>
          <p className="text-sm">
            Proof of concept using Vercel's useChat hook with Data Stream Protocol
          </p>
          <Button variant="ghost" onClick={() => setShowDebugInfo(prev => !prev)}>toggle debug</Button>
        </div>

        {showDebugInfo && <MessagesInfos messages={messages} />}

        <div className="flex-1 overflow-y-auto p-4 mb-4">
          {messages.length === 0 ? (
            <div className="text-center text-foreground/50 mt-8">
              <p>Start a conversation by typing a message below.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex w-full min-w-full ${message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                >
                  <div
                    className={`${message.role === 'user' ? 'p-3 rounded-2xl border border-zinc-300' : "w-full"}`}
                  >

                    <div className="whitespace-pre-wrap font-medium">{message.content}</div>

                    {message.role === 'assistant' && messageFiles[message.id] && !isLoading && (
                      <div className="mt-2">
                        <FilePanel files={messageFiles[message.id]} />
                      </div>
                    )}

                    {message.role === 'assistant' && message.parts && (
                      <div className="mt-3 w-full">
                        {message.parts
                          .filter((part: any) => part.type === 'reasoning')
                          .map((reasoningPart: any, index: number) => (
                            <Accordion key={index} type="single" collapsible className="w-full border border-zinc-300 rounded">
                              <AccordionItem value={`reasoning-${index}`} className="w-full">
                                <AccordionTrigger className="w-full font-medium px-6 py-3 hover:no-underline flex justify-between">
                                  <div className="flex items-center gap-2 font-bold">
                                    <ReasoningCogs className="text-zinc-700 size-3" />
                                    Mostrar Raciocínio
                                  </div>
                                </AccordionTrigger>
                                <AccordionContent className='px-6'>
                                  <div className="text-sm whitespace-pre-wrap">
                                    {reasoningPart.reasoning || reasoningPart.content || reasoningPart.text}
                                  </div>
                                </AccordionContent>
                              </AccordionItem>
                            </Accordion>
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
              <div className="flex items-center space-x-1">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
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

        <FormInput
          handleSubmit={handleSubmit}
          input={input}
          handleInputChange={handleInputChange}
          isLoading={isLoading}
        />

      </div>


    </div>
  );
}

const FormInput = ({
  handleSubmit,
  input,
  handleInputChange,
  isLoading
}: {
  handleSubmit: (event?: { preventDefault?: () => void }) => void;
  input: string;
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement> | React.ChangeEvent<HTMLTextAreaElement>) => void;
  isLoading: boolean;
}) => {
  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-center bg-white border border-zinc-300 rounded-full px-4 py-3  focus-within:border-zinc-700">
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="Type your message here..."
          disabled={isLoading}
          className="flex-1 bg-transparent text-zinc-700 placeholder:text-zinc-400 focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="ml-2 p-2 cursor-pointer bg-zinc-700 text-white rounded-full hover:bg-zinc-800 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ArrowRight size={16} />
        </button>
      </div>
    </form>

  )
}

const MessagesInfos = ({ messages }: { messages: UIMessage[] }) => {
  return (
    <div className={"flex-1 flex flex-col overflow-y-scroll max-h-1/2 text-xs"}>
      <div className="font-semibold mb-2">Message Debug Info:</div>
      {messages.map(message => (
        <div key={message.id} className='mb-2 p-2 border rounded'>
          <div><strong>ID:</strong> {message.id}</div>
          <div><strong>Role:</strong> {message.role}</div>
          <div><strong>Content:</strong> {message.content ? message.content.slice(0, 100) + '...' : 'None'}</div>
          <div><strong>Reasoning Parts:</strong> {(message as any).parts?.filter((p: any) => p.type === 'reasoning').length || 0}</div>
          <div><strong>Parts:</strong> {JSON.stringify((message as any).parts || 'None')}</div>
        </div>
      ))}
    </div>
  )
}
