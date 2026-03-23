export default function Sidebar({ documents, onUploadClick }) {
    return (
      <div className="w-64 bg-gray-900 flex flex-col border-r border-gray-800">
        {/* Logo */}
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xl font-bold text-white">🧠 RAG Chat</h1>
          <p className="text-xs text-gray-400 mt-1">Powered by Claude + AWS</p>
        </div>
  
        {/* Upload Button */}
        <div className="p-4">
          <button
            onClick={onUploadClick}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
          >
            <span>+</span> Upload PDF
          </button>
        </div>
  
        {/* Documents List */}
        <div className="flex-1 overflow-y-auto px-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Documents
          </p>
          {documents.length === 0 ? (
            <p className="text-xs text-gray-600 italic">No documents uploaded yet</p>
          ) : (
            <ul className="space-y-2">
              {documents.map((doc, i) => (
                <li
                  key={i}
                  className="flex items-center gap-2 text-sm text-gray-300 bg-gray-800 rounded-lg px-3 py-2"
                >
                  <span>📄</span>
                  <span className="truncate">{doc}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
  
        {/* Footer */}
        <div className="p-4 border-t border-gray-800">
          <p className="text-xs text-gray-600 text-center">
            Built with FastAPI · Pinecone · Bedrock
          </p>
        </div>
      </div>
    );
  }