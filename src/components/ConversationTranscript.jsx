import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

export default function ConversationTranscript({ messages, isTyping }) {
  const chatEndRef = useRef(null);

  useEffect(() => {
    // Smooth scroll with spring-like animation
    chatEndRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'end'
    });
  }, [messages, isTyping]);

  return (
    <div className="flex-1 overflow-y-auto p-4 scroll-smooth" style={{
      scrollBehavior: 'smooth',
      scrollPaddingBottom: '20px'
    }}>
      {/* Center messages on desktop with max-width */}
      <div className="max-w-3xl mx-auto space-y-3">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            style={{
              animation: `messageSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both`,
              animationDelay: '0ms'
            }}
          >
            <div
              className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-3.5 text-lg leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-200/50'
                  : 'bg-white text-gray-800 border border-gray-100 shadow-md'
              } transform transition-all duration-200 hover:scale-[1.01]`}
              dir="auto"
            >
              <ReactMarkdown
                components={{
                  // Headings
                  h1: ({node, ...props}) => <h1 className="text-2xl font-bold mb-2 mt-1" {...props} />,
                  h2: ({node, ...props}) => <h2 className="text-xl font-bold mb-2 mt-1" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-lg font-semibold mb-1 mt-1" {...props} />,

                  // Paragraphs
                  p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,

                  // Lists
                  ul: ({node, ...props}) => <ul className="list-disc list-inside mb-2 space-y-1" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />,
                  li: ({node, ...props}) => <li className="mr-2" {...props} />,

                  // Strong/Bold
                  strong: ({node, ...props}) => <strong className="font-bold" {...props} />,

                  // Emphasis/Italic
                  em: ({node, ...props}) => <em className="italic" {...props} />,

                  // Links
                  a: ({node, ...props}) => (
                    <a
                      className={`underline ${
                        msg.sender === 'user' ? 'text-white/90 hover:text-white' : 'text-indigo-600 hover:text-indigo-700'
                      }`}
                      target="_blank"
                      rel="noopener noreferrer"
                      {...props}
                    />
                  ),

                  // Code
                  code: ({node, inline, ...props}) =>
                    inline ? (
                      <code className={`px-1.5 py-0.5 rounded text-sm font-mono ${
                        msg.sender === 'user' ? 'bg-white/20' : 'bg-gray-100'
                      }`} {...props} />
                    ) : (
                      <code className={`block px-3 py-2 rounded my-2 text-sm font-mono ${
                        msg.sender === 'user' ? 'bg-white/20' : 'bg-gray-100'
                      }`} {...props} />
                    ),

                  // Blockquote
                  blockquote: ({node, ...props}) => (
                    <blockquote className={`border-r-4 pr-3 my-2 italic ${
                      msg.sender === 'user' ? 'border-white/40' : 'border-indigo-300'
                    }`} {...props} />
                  ),

                  // Horizontal Rule
                  hr: ({node, ...props}) => (
                    <hr className={`my-3 ${
                      msg.sender === 'user' ? 'border-white/30' : 'border-gray-200'
                    }`} {...props} />
                  ),
                }}
              >
                {msg.text}
              </ReactMarkdown>
            </div>
          </div>
        ))}

        {isTyping && (
          <div
            className="flex justify-start"
            style={{
              animation: 'messageSlideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both'
            }}
          >
            <div className="bg-white text-gray-800 border border-gray-100 shadow-md rounded-2xl px-5 py-3.5">
              <div className="flex gap-1.5 items-center">
                <div className="w-2.5 h-2.5 bg-indigo-400 rounded-full animate-bounce"></div>
                <div className="w-2.5 h-2.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                <div className="w-2.5 h-2.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      <style>{`
        @keyframes messageSlideIn {
          from {
            opacity: 0;
            transform: translateY(16px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
      `}</style>
    </div>
  );
}
