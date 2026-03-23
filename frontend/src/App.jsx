import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import UploadModal from "./components/UploadModal";

const API_URL = "http://52.201.242.255:8000";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [showUpload, setShowUpload] = useState(false);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (question) => {
    const userMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: 3 }),
      });
      const data = await res.json();
      const assistantMessage = {
        role: "assistant",
        content: data.answer,
        sources: data.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again.", sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onUploadSuccess = (filename) => {
    setDocuments((prev) => [...prev, filename]);
    setShowUpload(false);
  };

  return (
    <div className="flex h-screen bg-gray-950 text-white">
      <Sidebar
        documents={documents}
        onUploadClick={() => setShowUpload(true)}
      />
      <ChatWindow
        messages={messages}
        loading={loading}
        onSend={sendMessage}
      />
      {showUpload && (
        <UploadModal
          apiUrl={API_URL}
          onSuccess={onUploadSuccess}
          onClose={() => setShowUpload(false)}
        />
      )}
    </div>
  );
}