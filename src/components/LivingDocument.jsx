import React, { useState, useEffect, useRef } from 'react';
import {
  X, MessageCircle, ChevronDown, ChevronUp, Send, Loader2,
  CheckCircle, HelpCircle
} from 'lucide-react';
import { api } from '../api/client';

/**
 * LivingDocument - Living Dashboard Phase 3
 *
 * Renders an artifact with sections that can have threaded conversations.
 * Each section shows a thread indicator if conversations exist.
 *
 * Features:
 * - Structured artifact rendering (headings, paragraphs)
 * - Thread indicators on sections
 * - Inline thread expansion
 * - Contextual Q&A with AI
 */

// Thread indicator component
function ThreadIndicator({ count, hasUnread, onClick }) {
  if (count === 0) return null;

  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
        transition-all duration-200 hover:scale-105
        ${hasUnread
          ? 'bg-blue-100 text-blue-700 border border-blue-200'
          : 'bg-gray-100 text-gray-600 border border-gray-200'
        }
      `}
    >
      <MessageCircle className="w-3 h-3" />
      <span>{count}</span>
    </button>
  );
}

// Single thread message
function ThreadMessage({ message, isUser }) {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div
        className={`
          max-w-[85%] px-3 py-2 rounded-2xl text-sm
          ${isUser
            ? 'bg-indigo-500 text-white rounded-br-md'
            : 'bg-gray-100 text-gray-800 rounded-bl-md'
          }
        `}
      >
        {message.content}
      </div>
    </div>
  );
}

// Thread component (inline conversation)
function SectionThread({
  thread,
  onAddMessage,
  onResolve,
  isLoading
}) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [thread?.messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    onAddMessage(inputValue);
    setInputValue('');
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden mt-2">
      {/* Thread header */}
      <div
        className="flex items-center justify-between px-3 py-2 bg-gray-50 border-b cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <MessageCircle className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">
            {thread.preview || 'שיחה'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {thread.is_resolved && (
            <CheckCircle className="w-4 h-4 text-green-500" />
          )}
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>

      {/* Thread content */}
      {isExpanded && (
        <div className="p-3">
          {/* Messages */}
          <div className="max-h-60 overflow-y-auto mb-3">
            {(thread.messages || []).map((msg) => (
              <ThreadMessage
                key={msg.message_id}
                message={msg}
                isUser={msg.role === 'user'}
              />
            ))}
            <div ref={messagesEndRef} />

            {isLoading && (
              <div className="flex justify-start mb-2">
                <div className="bg-gray-100 px-3 py-2 rounded-2xl rounded-bl-md">
                  <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          {!thread.is_resolved && (
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="שאלו שאלה נוספת..."
                className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-200"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="p-2 bg-indigo-500 text-white rounded-full hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* Resolve button */}
          {!thread.is_resolved && (thread.messages?.length || 0) > 1 && (
            <button
              onClick={onResolve}
              className="mt-2 w-full py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded transition"
            >
              הבנתי, תודה
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// Section component with thread support
function DocumentSection({
  section,
  threads,
  onCreateThread,
  onAddMessage,
  onResolve,
  isLoadingThread
}) {
  const [showNewThread, setShowNewThread] = useState(false);
  const [newQuestion, setNewQuestion] = useState('');

  const sectionThreads = threads.filter(t => t.section_id === section.section_id);
  const threadCount = sectionThreads.length;

  const handleCreateThread = (e) => {
    e.preventDefault();
    if (!newQuestion.trim()) return;

    onCreateThread(section, newQuestion);
    setNewQuestion('');
    setShowNewThread(false);
  };

  // Determine section styling based on type
  const isHeading = section.section_type === 'heading';
  const headingLevel = section.level || 2;

  return (
    <div
      className={`relative mb-4 p-3 -mx-3 rounded-xl transition-all duration-150 ${
        showNewThread
          ? 'bg-indigo-50/50'
          : 'cursor-pointer hover:bg-gradient-to-r hover:from-indigo-50/70 hover:to-purple-50/50 hover:shadow-md hover:-translate-y-px border border-transparent hover:border-indigo-100/50'
      }`}
      onClick={() => !showNewThread && setShowNewThread(true)}
    >
      {/* Section content */}
      <div className="flex-1">
        {isHeading ? (
          <div>
            {/* Heading with thread indicator */}
            <div className="flex items-center gap-2 mb-2">
              {headingLevel === 1 && (
                <h1 className="text-2xl font-bold text-gray-900">{section.title}</h1>
              )}
              {headingLevel === 2 && (
                <h2 className="text-xl font-semibold text-gray-800">{section.title}</h2>
              )}
              {headingLevel >= 3 && (
                <h3 className="text-lg font-medium text-gray-700">{section.title}</h3>
              )}
              <ThreadIndicator
                count={threadCount}
                hasUnread={sectionThreads.some(t => !t.is_resolved)}
                onClick={() => {}}
              />
            </div>
            {/* Section content below heading */}
            {section.content && (
              <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {section.content}
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
            {section.content}
          </div>
        )}
      </div>

      {/* New thread input */}
      {showNewThread && (
        <form
          onSubmit={handleCreateThread}
          onClick={(e) => e.stopPropagation()}
          className="mt-2 p-3 bg-indigo-50 rounded-lg border border-indigo-100 animate-springIn origin-top"
        >
          <div className="flex items-center gap-2 mb-2">
            <MessageCircle className="w-4 h-4 text-indigo-500" />
            <span className="text-sm font-medium text-indigo-700">שאלה על קטע זה</span>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={newQuestion}
              onChange={(e) => setNewQuestion(e.target.value)}
              placeholder="מה תרצו לדעת על הקטע הזה?"
              className="flex-1 px-3 py-2 text-sm border border-indigo-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
              autoFocus
            />
            <button
              type="submit"
              disabled={!newQuestion.trim()}
              className="px-3 py-2 bg-indigo-500 text-white text-sm rounded-lg hover:bg-indigo-600 disabled:opacity-50 transition"
            >
              שאל
            </button>
            <button
              type="button"
              onClick={() => setShowNewThread(false)}
              className="px-3 py-2 text-gray-500 text-sm hover:bg-gray-100 rounded-lg transition"
            >
              ביטול
            </button>
          </div>
        </form>
      )}

      {/* Existing threads */}
      {sectionThreads.map((thread) => (
        <SectionThread
          key={thread.thread_id}
          thread={thread}
          onAddMessage={(content) => onAddMessage(thread.thread_id, content)}
          onResolve={() => onResolve(thread.thread_id)}
          isLoading={isLoadingThread === thread.thread_id}
        />
      ))}
    </div>
  );
}

export default function LivingDocument({
  familyId,
  artifactId,
  title,
  onClose
}) {
  const [structured, setStructured] = useState(null);
  const [threads, setThreads] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingThread, setLoadingThread] = useState(null);
  const [error, setError] = useState(null);

  // Fetch structured artifact and threads
  useEffect(() => {
    async function fetchData() {
      if (!familyId || !artifactId) return;

      try {
        setIsLoading(true);
        setError(null);

        // Fetch structured artifact
        const structuredData = await api.getStructuredArtifact(familyId, artifactId);
        setStructured(structuredData);

        // Fetch threads
        const threadsData = await api.getArtifactThreads(familyId, artifactId);
        setThreads(threadsData.threads || []);
      } catch (err) {
        console.error('Error fetching living document:', err);
        setError('שגיאה בטעינת המסמך');
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, [familyId, artifactId]);

  // Create new thread
  const handleCreateThread = async (section, question) => {
    try {
      setLoadingThread('creating');

      const result = await api.createThread(
        familyId,
        artifactId,
        section.section_id,
        question,
        section.title,
        section.content?.substring(0, 500)
      );

      // Add new thread to list
      const newThread = {
        thread_id: result.thread_id,
        section_id: section.section_id,
        messages: result.messages,
        preview: question.substring(0, 50),
        is_resolved: false
      };

      setThreads(prev => [...prev, newThread]);

      // Generate AI response
      setLoadingThread(result.thread_id);
      const responseResult = await api.addThreadMessage(
        result.thread_id,
        familyId,
        question
      );

      // Wait for the initial AI response to the first question
      // The API already added the AI response in createThread

    } catch (err) {
      console.error('Error creating thread:', err);
    } finally {
      setLoadingThread(null);
    }
  };

  // Add message to thread
  const handleAddMessage = async (threadId, content) => {
    try {
      setLoadingThread(threadId);

      const result = await api.addThreadMessage(threadId, familyId, content);

      // Update thread with new messages
      setThreads(prev => prev.map(t => {
        if (t.thread_id === threadId) {
          return {
            ...t,
            messages: [
              ...t.messages,
              result.user_message,
              ...(result.assistant_message ? [result.assistant_message] : [])
            ]
          };
        }
        return t;
      }));
    } catch (err) {
      console.error('Error adding message:', err);
    } finally {
      setLoadingThread(null);
    }
  };

  // Resolve thread
  const handleResolve = async (threadId) => {
    try {
      await api.resolveThread(threadId, artifactId);

      setThreads(prev => prev.map(t => {
        if (t.thread_id === threadId) {
          return { ...t, is_resolved: true };
        }
        return t;
      }));
    } catch (err) {
      console.error('Error resolving thread:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 animate-backdropIn">
      <div className="absolute inset-0 bg-black/50" />
      <div className="absolute inset-x-0 bottom-0 top-0 sm:top-8 sm:bottom-8 sm:left-8 sm:right-8 bg-white sm:rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-panelUp">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-800">
              {title || structured?.title || 'מסמך'}
            </h2>
            {structured?.total_threads > 0 && (
              <p className="text-sm text-gray-500">
                {structured.total_threads} שיחות
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-500">{error}</p>
            </div>
          ) : structured?.sections ? (
            <div className="max-w-3xl mx-auto">
              {/* Hint banner - show only if no threads exist yet */}
              {threads.length === 0 && (
                <p className="mb-6 text-sm text-gray-400 text-center">
                  לחצו על קטע כדי לשאול שאלה
                </p>
              )}

              {/* Render sections */}
              {structured.sections.map((section) => (
                <DocumentSection
                  key={section.section_id}
                  section={section}
                  threads={threads}
                  onCreateThread={handleCreateThread}
                  onAddMessage={handleAddMessage}
                  onResolve={handleResolve}
                  isLoadingThread={loadingThread}
                />
              ))}
            </div>
          ) : structured?.raw_content ? (
            // Fallback to raw content
            <div className="max-w-3xl mx-auto prose prose-gray">
              <div
                className="whitespace-pre-wrap"
                dangerouslySetInnerHTML={{
                  __html: structured.raw_content
                    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
                    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
                    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
                }}
              />
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <p>אין תוכן להצגה</p>
            </div>
          )}
        </div>
      </div>

      {/* Local animations (springIn for thread input) */}
      <style>{`
        @keyframes springIn {
          0% {
            opacity: 0;
            transform: scaleY(0.95) translateY(-2px);
          }
          70% {
            transform: scaleY(1.005) translateY(0);
          }
          100% {
            opacity: 1;
            transform: scaleY(1) translateY(0);
          }
        }
        .animate-springIn {
          animation: springIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
      `}</style>
    </div>
  );
}
