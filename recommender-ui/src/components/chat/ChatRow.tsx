import React, { useState, useEffect } from 'react';
import { LogoDwarves, LogoUser } from '../common/Logo';
import { LoadingDots } from '../common/LoadingDots';
import { MarkdownRenderer } from './MarkdownRenderer';
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from '@/components/ui/accordion';

interface ChatRowProps {
    message: string;
    isUser: boolean;
    bgColor: string;
    isLoading: boolean;
    isStreaming: boolean;
    agentThought?: string;
    finalResponse?: string;
    error?: string;
    isFirstMessage: boolean;
}

export const ChatRow = ({
    message,
    isUser,
    bgColor,
    isLoading,
    isStreaming,
    agentThought,
    finalResponse,
    error,
    isFirstMessage,
}: ChatRowProps) => {
    const [isAccordionOpen, setIsAccordionOpen] = useState(false);
    const [isAutoControlled, setIsAutoControlled] = useState(true);
    const showAccordions = !isFirstMessage && !isUser;

    useEffect(() => {
        if (isAutoControlled) {
            if (isStreaming && agentThought) {
                setIsAccordionOpen(true);
            } else if (!isStreaming && agentThought) {
                setIsAccordionOpen(false);
            }
        }
    }, [isStreaming, agentThought, isAutoControlled]);

    const handleAccordionToggle = (value: string) => {
        setIsAutoControlled(false);
        setIsAccordionOpen(value === 'item-1');
    };

    return (
        <div
            className={`flex ${
                isUser ? 'justify-end' : 'justify-start'
            } mb-4 w-full`}
        >
            <div
                className={`flex flex-col ${
                    isUser ? 'items-end' : 'items-start'
                } max-w-[80%]`}
            >
                <div
                    className={`flex items-start ${
                        isUser ? 'flex-row-reverse' : ''
                    }`}
                >
                    <div className="w-8 h-8 flex-shrink-0 mt-1">
                        {isUser ? <LogoUser /> : <LogoDwarves />}
                    </div>
                    <div
                        className={`mx-2 py-3 px-4 ${bgColor} rounded-lg ${
                            isUser ? 'rounded-tr-none' : 'rounded-tl-none'
                        } break-words flex-grow flex-col space-y-4`}
                    >
                        {isLoading && !isStreaming ? (
                            <LoadingDots />
                        ) : (
                            <>
                                {!isUser && (
                                    <>
                                        {showAccordions && agentThought && (
                                            <Accordion
                                                type="single"
                                                collapsible
                                                className="w-full border-1 px-4 rounded-md bg-white"
                                                value={
                                                    isAccordionOpen
                                                        ? 'item-1'
                                                        : ''
                                                }
                                                onValueChange={
                                                    handleAccordionToggle
                                                }
                                            >
                                                <AccordionItem value="item-1">
                                                    <AccordionTrigger className="py-2">
                                                        Agent Thought
                                                    </AccordionTrigger>
                                                    <AccordionContent>
                                                        <MarkdownRenderer
                                                            content={
                                                                agentThought
                                                            }
                                                            isStreaming={
                                                                isStreaming
                                                            }
                                                        />
                                                    </AccordionContent>
                                                </AccordionItem>
                                            </Accordion>
                                        )}

                                        {finalResponse ? (
                                            <MarkdownRenderer
                                                content={finalResponse}
                                                isStreaming={isStreaming}
                                            />
                                        ) : (
                                            <MarkdownRenderer
                                                content={message}
                                                isStreaming={isStreaming}
                                            />
                                        )}

                                        {error && (
                                            <div className="text-red-500">
                                                Error: {error}
                                            </div>
                                        )}
                                    </>
                                )}
                                {isUser && (
                                    <MarkdownRenderer
                                        content={message}
                                        isStreaming={false}
                                    />
                                )}
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
