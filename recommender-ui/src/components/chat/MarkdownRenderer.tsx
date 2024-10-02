import { useState, useEffect, useRef } from 'react';
import ReactMarkdown, { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';

interface MarkdownRendererProps {
    content: string;
    isStreaming?: boolean;
}

export const MarkdownRenderer = ({
    content,
    isStreaming,
}: MarkdownRendererProps) => {
    const [processedContent, setProcessedContent] = useState('');

    useEffect(() => {
        if (isStreaming) {
            const lines = content.split('\n');
            const uniqueLines = lines.filter(
                (line, index) => lines.indexOf(line) === index
            );
            setProcessedContent(uniqueLines.join('\n'));
        } else {
            setProcessedContent(content);
        }
    }, [content, isStreaming]);

    const components: Components = {
        h3: ({ ...props }) => (
            <h3
                className="text-xl font-medium my-2 text-indigo-600"
                {...props}
            />
        ),

        h4: ({ ...props }) => (
            <h4
                className="text-lg font-medium my-2 text-indigo-500"
                {...props}
            />
        ),

        p: ({ ...props }) => (
            <p className="leading-relaxed text-gray-700" {...props} />
        ),

        ul: ({ ...props }) => <ul className="list-disc pl-6" {...props} />,

        ol: ({ ...props }) => <ol className="list-decimal pl-6" {...props} />,

        li: ({ ...props }) => <li className="mb-1" {...props} />,

        blockquote: ({ ...props }) => (
            <blockquote
                className="border-l-2 border-indigo-500 pl-4 italic my-4 text-gray-600"
                {...props}
            />
        ),

        a: ({ ...props }) => (
            <a className="text-blue-500 hover:underline" {...props} />
        ),

        code({ inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            const codeString = String(children).replace(/\n$/, '');
            return !inline && match ? (
                <SyntaxHighlighter
                    style={atomDark}
                    language={match[1]}
                    PreTag="div"
                    className="mockup-code no-scrollbar"
                    showLineNumbers={true}
                    {...props}
                >
                    {codeString}
                </SyntaxHighlighter>
            ) : (
                <code className={className} {...props}>
                    {children}
                </code>
            );
        },

        pre({ children }: any) {
            return <div className="relative overflow-x-auto">{children}</div>;
        },

        hr: ({ ...props }) => (
            <hr className="my-4 border-t-2 border-gray-200" {...props} />
        ),

        table: ({ ...props }) => (
            <div className="overflow-x-auto no-scrollbar">
                <table className="my-2" {...props} />
            </div>
        ),

        thead: ({ ...props }) => <thead {...props} />,
        tbody: ({ ...props }) => <tbody {...props} />,
        tr: ({ ...props }) => <tr {...props} />,
        th: ({ ...props }) => <th {...props} />,
        td: ({ ...props }) => <td {...props} />,
    };

    return (
        <div className="prose prose-zinc dark:prose-invert scroll-smooth focus:scroll-auto text-sm">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
                {processedContent}
            </ReactMarkdown>
        </div>
    );
};
