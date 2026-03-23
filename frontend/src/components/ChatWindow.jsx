import { useState, useRef, useEffect } from "react";

function SourceCarousel({ sources }) {
  const [current, setCurrent] = useState(0);
  const source = sources[current];

  return (
    <div className="mt-3 bg-gray-800 border border-gray-700 rounded-xl p-3 text-xs text-gray-300">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-gray-500 font-medium">Sources</p>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrent((prev) => Math.max(prev - 1, 0))}
            disabled={current === 0}
            className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-700 hover:bg-gray-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ‹
          </button>
          <span className="text-gray-500">{current + 1} / {sources.length}</span>
          <button
            onClick={() => setCurrent((prev) => Math.min(prev + 1, sources.length - 1))}
            disabled={current === sources.length - 1}
            className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-700 hover:bg-gray-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ›
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-indigo-400 truncate">
          📄 {source.filename || source.source?.split("/").pop() || "Document"}
        </span>
        {source.rerank_score && (
          <span className="ml-2 bg-indigo-900 text-indigo-300 px-2 py-0.5 rounded-full text-xs whitespace-nowrap">
            {(source.rerank_score * 100).toFixed(0)}% match
          </span>
        )}
      </div>
      <p className="text-gray-400 line-clamp-3">{source.text}</p>
      <p className="text-gray-600 mt-1">Page {source.page}</p>
    </div>
  );
}

function Message({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div className="max-w-xl w-full flex flex-col">
        <span className={`text-xs text-gray-500 mb-1 px-1 ${isUser ? "text-right" : "text-left"}`}>
          {isUser ? "You" : "🤖 Claude"}
        </span>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-indigo-600 text-white rounded-tr-sm self-end"
              : "bg-gray-800 text-gray-100 rounded-tl-sm"
          }`}
        >
          {message.content}
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <SourceCarousel sources={message.sources} />
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex gap-1 items-center h-4">
          <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
          <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
          <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  );
}

export default function ChatWindow({ messages, loading, onSend }) {
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <h2 className="text-sm font-semibold text-white">Document Chat</h2>
        <p className="text-xs text-gray-500">Ask anything about your uploaded documents</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-6">
        <div className="max-w-xl mx-auto px-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center pt-32">
              <div className="text-5xl mb-4">🧠</div>
              <h3 className="text-lg font-semibold text-gray-300 mb-2">
                Ask your documents anything
              </h3>
              <p className="text-sm text-gray-500 max-w-sm">
                Upload a PDF using the sidebar, then ask questions and get AI-powered answers with source citations.
              </p>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <Message key={i} message={msg} />
              ))}
              {loading && <TypingIndicator />}
            </>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-gray-900 border-t border-gray-800 px-6 py-4">
        <div className="max-w-xl mx-auto">
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              rows={1}
              className="flex-1 bg-gray-800 text-white text-sm rounded-xl px-4 py-3 resize-none outline-none border border-gray-700 focus:border-indigo-500 transition-colors placeholder-gray-500"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-3 rounded-xl transition-colors duration-200 text-sm font-medium"
            >
              Send
            </button>
          </div>
          <p className="text-xs text-gray-600 mt-2">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  );
}