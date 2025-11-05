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
              className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-3.5 text-base leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-200/50'
                  : 'bg-white text-gray-800 border border-gray-100 shadow-md'
              } transform transition-all duration-200 hover:scale-[1.01] markdown-content`}
            >
              <ReactMarkdown
                components={{
                  // Custom renderers for markdown elements
                  p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-bold" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-none pr-4 my-2 space-y-1" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal pr-6 my-2 space-y-1" {...props} />,
                  li: ({node, ...props}) => <li className="text-sm" {...props} />,
                  h1: ({node, ...props}) => <h1 className="text-xl font-bold mb-2" {...props} />,
                  h2: ({node, ...props}) => <h2 className="text-lg font-bold mb-2 mt-3" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-base font-bold mb-1 mt-2" {...props} />,
                  a: ({node, ...props}) => <a className="underline hover:opacity-80" {...props} />,
                  code: ({node, inline, ...props}) =>
                    inline
                      ? <code className="bg-gray-100 px-1 rounded text-sm" {...props} />
                      : <code className="block bg-gray-100 p-2 rounded my-2 text-sm" {...props} />
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
