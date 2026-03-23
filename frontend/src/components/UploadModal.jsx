import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";

export default function UploadModal({ apiUrl, onSuccess, onClose }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState("");

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    setProgress("Uploading PDF...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      setProgress("Ingesting into vector store...");
      const res = await fetch(`${apiUrl}/ingest`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }

      setProgress("Done!");
      setTimeout(() => onSuccess(file.name), 500);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }, [apiUrl, onSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">Upload Document</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors text-xl"
          >
            ✕
          </button>
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors duration-200 ${
            isDragActive
              ? "border-indigo-500 bg-indigo-950"
              : "border-gray-700 hover:border-indigo-600 hover:bg-gray-800"
          } ${uploading ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          <input {...getInputProps()} />
          <div className="text-4xl mb-3">📄</div>
          {uploading ? (
            <div>
              <p className="text-sm text-indigo-400 font-medium">{progress}</p>
              <div className="mt-3 w-full bg-gray-700 rounded-full h-1.5">
                <div className="bg-indigo-500 h-1.5 rounded-full animate-pulse w-3/4" />
              </div>
            </div>
          ) : isDragActive ? (
            <p className="text-sm text-indigo-400">Drop your PDF here...</p>
          ) : (
            <div>
              <p className="text-sm text-gray-300 font-medium">
                Drag & drop a PDF here
              </p>
              <p className="text-xs text-gray-500 mt-1">or click to browse</p>
              <p className="text-xs text-gray-600 mt-3">PDF files only · Max 1 file</p>
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 bg-red-950 border border-red-800 rounded-lg px-4 py-3">
            <p className="text-sm text-red-400">⚠️ {error}</p>
          </div>
        )}
      </div>
    </div>
  );
}