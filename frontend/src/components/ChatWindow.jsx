import { useState, useRef, useEffect } from "react";

function SourceCard({ source }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 text-xs text-gray-300">
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
      <p className="text-gray-400 line-clamp-2">{source.text}</p>
      <p className="text-gray-600 mt-1">Page {source.page}</p>
    </div>
  );
}

function Message({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-6`}>
      <div className={`max-w-2xl ${isUser ? "order-2" : "order-1"}`}>
        {/* Avatar */}
        <div className={`flex items-center gap-2 mb-2 ${isUser ? "justify-end" : "justify-start"}`}>
          <span className="text-xs text-gray-500">
            {isUser ? "You" : "🤖 Claude"}
          </span>
        </div>

        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-indigo-600 text-white rounded-tr-sm"
              : "bg-gray-800 text-gray-100 rounded-tl-sm"
          }`}
        >
          {message.content}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 space-y-2">
            <p className="text-xs text-gray-500 font-medium">Sources used:</p>
            {message.sources.map((source, i) => (
              <SourceCard key={i} source={source} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-6">
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
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <h2 className="text-sm font-semibold text-white">Document Chat</h2>
        <p className="text-xs text-gray-500">Ask anything about your uploaded documents</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
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

      {/* Input */}
      <div className="bg-gray-900 border-t border-gray-800 px-6 py-4">
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
  );
}