// frontend/src/components/common/ChatInput.tsx
import React, { useState, useRef, useEffect } from 'react';
import { SendHorizontal } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  isLoading = false,
  placeholder = "Ask anything about your data... (Shift+Enter for new line)"
}) => {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // --- THE MAGIC AUTO-RESIZE LOGIC ---
  const adjustHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      // Reset height to get the correct scrollHeight
      textarea.style.height = "auto";
      // Set new height based on scroll height, but cap it at 200px
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

  // Adjust height whenever the input value changes
  useEffect(() => {
    adjustHeight();
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (but NOT Shift+Enter)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // Prevents adding a new line
      handleSend();
    }
  };

  const handleSend = () => {
    if (input.trim() === "" || isLoading) return;
    onSend(input.trim());
    setInput(""); // Clear input
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  return (
    <div className="flex items-end gap-2 p-2.5 sm:p-3 bg-slate-900/90 rounded-2xl border border-sky-400/30 focus-within:border-sky-400 focus-within:ring-2 focus-within:ring-sky-500/20 shadow-lg shadow-sky-500/10 transition-all">
      {/* The Auto-Expanding Textarea */}
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        disabled={isLoading}
        className="flex-1 bg-transparent text-white placeholder-slate-400/80 resize-none outline-none text-sm max-h-[200px] py-1.5 pl-2 custom-scrollbar disabled:opacity-50"
        style={{ overflowY: 'auto' }}
      />

      {/* Send Button */}
      <button
        type="button"
        onClick={handleSend}
        disabled={input.trim() === "" || isLoading}
        className="p-2.5 rounded-xl bg-gradient-to-r from-sky-400 to-blue-500 text-slate-950 hover:text-white font-bold hover:from-sky-500 hover:to-blue-600 shadow-md shadow-sky-500/20 transition-all disabled:opacity-30 disabled:cursor-not-allowed flex-shrink-0 mb-0.5"
        title="Send query (Enter)"
      >
        <SendHorizontal className="w-5 h-5" />
      </button>
    </div>
  );
};
