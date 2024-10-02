'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import { ChatRow } from '@/components/chat/ChatRow';
import { BackgroundDots } from '@/components/common/BackgroundDot';
import { Dot } from '@/components/common/Dot';
import { LoadingDots } from '@/components/common/LoadingDots';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { SideBar } from '@/components/Sidebar';
import { GPTIcon, CLAUDEIcon } from '@/components/svg';

interface Message {
    message_id: string;
    content: string;
    isUser: boolean;
    isStreaming: boolean;
    isLoading: boolean;
    timestamp: string;
    agentThought?: string;
    finalResponse?: string;
    error?: string;
}

interface ModelConfig {
    provider: string;
    model: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api';

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([
        {
            message_id: '0',
            content: 'Hi there. May I help you with anything?',
            isUser: false,
            isStreaming: false,
            isLoading: false,
            timestamp: new Date().toISOString(),
        },
    ]);
    const [input, setInput] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [modelConfig, setModelConfig] = useState<ModelConfig | null>(null);
    const [isModelConfigured, setIsModelConfigured] = useState(false);
    const socketRef = useRef<WebSocket | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const fetchModelConfig = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/api/model-config`);
            if (response.ok) {
                const data = await response.json();
                setModelConfig(data);
                setIsModelConfigured(!!data.provider && !!data.model);
                console.log('Model configuration fetched:', data);
            } else {
                console.error('Failed to fetch model configuration');
            }
        } catch (error) {
            console.error('Error fetching model configuration:', error);
        }
    }, []);

    useEffect(() => {
        fetchModelConfig();
    }, [fetchModelConfig]);

    const connectWebSocket = useCallback(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.close();
        }

        const wsProtocol =
            window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (!token) {
            console.error('No token found in URL');
            return;
        }
        const wsUrl = `${wsProtocol}//${
            window.location.host
        }/api/ws/chat?token=${encodeURIComponent(token)}`;
        console.log('Attempting to connect to WebSocket:', wsUrl);
        socketRef.current = new WebSocket(wsUrl);

        socketRef.current.onopen = () => {
            console.log('WebSocket connection established');
            setIsConnected(true);
        };

        socketRef.current.onmessage = (event) => {
            console.log('Received message:', event.data);
            const data = JSON.parse(event.data);
            setMessages((prevMessages) => {
                const updatedMessages = [...prevMessages];
                const lastMessage = updatedMessages[updatedMessages.length - 1];

                const updateOrCreateMessage = (
                    newContent: Partial<Message>
                ) => {
                    if (lastMessage && !lastMessage.isUser) {
                        return [
                            ...updatedMessages.slice(0, -1),
                            {
                                ...lastMessage,
                                ...newContent,
                                agentThought: newContent.agentThought
                                    ? (lastMessage.agentThought || '') +
                                      newContent.agentThought
                                    : lastMessage.agentThought,
                                finalResponse: newContent.finalResponse
                                    ? (lastMessage.finalResponse || '') +
                                      newContent.finalResponse
                                    : lastMessage.finalResponse,
                                content: newContent.content
                                    ? (lastMessage.content || '') +
                                      newContent.content
                                    : lastMessage.content,
                                isStreaming:
                                    newContent.isStreaming !== undefined
                                        ? newContent.isStreaming
                                        : lastMessage.isStreaming,
                                isLoading:
                                    newContent.isLoading !== undefined
                                        ? newContent.isLoading
                                        : lastMessage.isLoading,
                            },
                        ];
                    }
                    return [
                        ...updatedMessages,
                        {
                            message_id: data.message_id,
                            content: '',
                            isUser: false,
                            isStreaming: false,
                            isLoading: false,
                            timestamp: data.timestamp,
                            ...newContent,
                        },
                    ];
                };

                switch (data.type) {
                    case 'error':
                        return updateOrCreateMessage({
                            error: data.content,
                            isLoading: false,
                            isStreaming: false,
                        });
                    case 'agent_thought':
                        return updateOrCreateMessage({
                            agentThought: data.content,
                            isLoading: false,
                            isStreaming: true,
                        });
                    case 'final_response':
                        return updateOrCreateMessage({
                            finalResponse: data.content,
                            content: data.content,
                            isLoading: false,
                            isStreaming: false,
                        });
                    case 'end':
                        if (lastMessage && !lastMessage.isUser) {
                            return [
                                ...updatedMessages.slice(0, -1),
                                {
                                    ...lastMessage,
                                    isStreaming: false,
                                    isLoading: false,
                                },
                            ];
                        }
                        return updatedMessages;
                    default:
                        return updatedMessages;
                }
            });
            if (data.type === 'end') {
                setIsLoading(false);
            }
        };

        socketRef.current.onerror = (error) => {
            console.error('WebSocket error:', error);
            setIsConnected(false);
        };

        socketRef.current.onclose = (event) => {
            console.log(
                'WebSocket connection closed:',
                event.code,
                event.reason
            );
            setIsConnected(false);
            setTimeout(connectWebSocket, 3000);
        };
    }, [setMessages, setIsConnected, setIsLoading]);

    useEffect(() => {
        if (isModelConfigured) {
            console.log('Model configured, attempting to connect WebSocket');
            connectWebSocket();
        }
    }, [isModelConfigured, connectWebSocket]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && isConnected && !isLoading) {
            sendMessage(input);
            setInput('');
            setIsLoading(true);
        }
    };

    const sendMessage = (message: string) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            console.log('Sending message:', message);
            const timestamp = new Date().toISOString();
            setMessages((prev) => [
                ...prev,
                {
                    message_id: `user-${Date.now()}`,
                    content: message,
                    isUser: true,
                    isStreaming: false,
                    isLoading: false,
                    timestamp: timestamp,
                },
            ]);
            socketRef.current.send(
                JSON.stringify({ content: message, timestamp: timestamp })
            );
        } else {
            console.error('WebSocket is not connected');
            setMessages((prev) => [
                ...prev,
                {
                    message_id: `error-${Date.now()}`,
                    content: 'Error: Unable to send message. Please try again.',
                    isUser: false,
                    isStreaming: false,
                    isLoading: false,
                    timestamp: new Date().toISOString(),
                },
            ]);
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-screen">
            <BackgroundDots className="absolute inset-0 z-0" />
            <SideBar onConfigured={fetchModelConfig} />
            <div className="flex-grow mt-8 z-10 relative items-center">
                <div className="max-w-5xl mx-auto">
                    <div className="drop-shadow-lg rounded-lg overflow-hidden">
                        <div className="h-[calc(100vh-11rem)] overflow-y-auto p-8 bg-white no-scrollbar">
                            {messages.map((message, index) => (
                                <ChatRow
                                    key={message.message_id}
                                    message={message.content}
                                    isUser={message.isUser}
                                    bgColor={
                                        message.isUser
                                            ? 'bg-blue-100'
                                            : 'bg-gray-100'
                                    }
                                    isStreaming={message.isStreaming}
                                    isLoading={message.isLoading}
                                    agentThought={message.agentThought}
                                    finalResponse={message.finalResponse}
                                    error={message.error}
                                    isFirstMessage={index === 0}
                                />
                            ))}
                            <div ref={messagesEndRef} />
                        </div>
                        <form onSubmit={handleSubmit} className="p-4 bg-white">
                            <div className="flex bg-white">
                                <Input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Ask for anything"
                                    className="flex-grow mr-2 bg-gray-100"
                                    disabled={
                                        !isModelConfigured ||
                                        !isConnected ||
                                        isLoading
                                    }
                                />
                                <Button
                                    type="submit"
                                    disabled={
                                        !isModelConfigured ||
                                        !isConnected ||
                                        isLoading
                                    }
                                    className="bg-blue-500 hover:bg-blue-600 text-white"
                                >
                                    {isLoading ? <LoadingDots /> : 'Send'}
                                </Button>
                            </div>
                        </form>
                        <div className="px-6 py-2 space-x-4 text-sm text-gray-500 border-gray-200 bg-white flex items-center">
                            <div className="flex items-center">
                                <Dot status={isConnected} />
                                <p>Connection</p>
                            </div>
                            <div className="flex items-center">
                                <Dot status={isLoading} />
                                <p>Generating</p>
                            </div>
                            {modelConfig && (
                                <div className="flex items-center">
                                    {modelConfig.provider === 'openai' && (
                                        <GPTIcon className="w-5 h-5 mr-2" />
                                    )}
                                    {modelConfig.provider === 'anthropic' && (
                                        <CLAUDEIcon className="w-5 h-5 mr-2" />
                                    )}
                                    <p>{`${modelConfig.model}`}</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
