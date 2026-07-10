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
      const currentScrollY = window.scrollY;
      // Reset height to get the correct scrollHeight
      textarea.style.height = "auto";
      // Set new height based on scroll height, but cap it at 200px
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
      if (window.scrollY !== currentScrollY) {
        window.scrollTo(0, currentScrollY);
      }
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
    <div className="flex flex-col gap-1.5 w-full">
      <div className="flex items-center gap-2 px-1 text-xs font-bold text-sky-300 tracking-wide">
        <span className="inline-block w-2 h-2 rounded-full bg-sky-400 animate-ping mr-1" />
        <span>Ask AI Statistical Consultant & Copilot:</span>
      </div>
      <div className="flex items-end gap-2.5 p-3 sm:p-3.5 bg-gradient-to-r from-slate-900/95 via-slate-950 to-purple-950/40 rounded-2xl border-2 border-sky-400/70 focus-within:border-sky-300 focus-within:ring-4 focus-within:ring-sky-400/30 shadow-2xl shadow-sky-500/20 transition-all">
        {/* The Auto-Expanding Textarea */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={isLoading}
          className="flex-1 bg-transparent text-white placeholder-slate-400 font-medium resize-none outline-none text-sm sm:text-base max-h-[200px] py-1.5 pl-2 custom-scrollbar disabled:opacity-50"
          style={{ overflowY: 'auto' }}
        />

        {/* Send Button with Light Blue (Sky) Arrow */}
        <button
          type="button"
          onClick={handleSend}
          disabled={input.trim() === "" || isLoading}
          className="p-3 rounded-xl bg-sky-400 hover:bg-sky-300 text-slate-950 font-extrabold shadow-lg shadow-sky-400/50 hover:scale-105 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100 flex-shrink-0 mb-0.5"
          title="Send query (Enter)"
        >
          <SendHorizontal className="w-5 h-5 stroke-[2.5]" />
        </button>
      </div>
    </div>
  );
};
