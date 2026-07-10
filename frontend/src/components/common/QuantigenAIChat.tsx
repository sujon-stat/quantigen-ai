import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, Bot, User, ArrowRight, Lightbulb, AlertCircle } from 'lucide-react';
import { api } from '../../api/client';
import { ChatInput } from './ChatInput';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  suggestedActions?: string[];
  timestamp?: string;
}

interface QuantigenAIChatProps {
  context?: Record<string, any>;
  initialMessages?: ChatMessage[];
  title?: string;
  subtitle?: string;
  onExecuteMethod?: (methodId: string) => void;
  hideHeader?: boolean;
}

const getDynamicSuggestions = (ctx: Record<string, any>): string[] => {
  const cols: any[] = ctx.columns_metadata || (ctx.dataset as any)?.columns || (ctx.dataset as any)?.variables || [];
  const analysis = ctx.current_analysis || (ctx.response as any);

  if (analysis && analysis.method_name) {
    return [
      `Explain what the results for ${analysis.method_name} mean in APA 7th`,
      `How did the Assumption Shield verify diagnostic criteria for ${analysis.method_name}?`,
      `Explain p-values & statistical significance`,
      `Suggest my next statistical step based on these results`
    ];
  }

  if (cols.length > 0) {
    const contCol = cols.find((c: any) => c.type === 'continuous' || c.data_type === 'numeric' || c.scale === 'continuous');
    const catCol = cols.find((c: any) => c.type === 'categorical' || c.data_type === 'string' || c.scale === 'nominal');
    const firstCol = cols[0];
    const secondCol = cols.length > 1 ? cols[1] : firstCol;

    const suggestions: string[] = [];
    if (contCol) {
      suggestions.push(`Explain skewness and normality checks for ${contCol.name || contCol.id}`);
    } else if (firstCol) {
      suggestions.push(`Examine statistical properties of ${firstCol.name || firstCol.id}`);
    }

    if (catCol) {
      suggestions.push(`Check frequency distribution and unique levels for ${catCol.name || catCol.id}`);
    } else if (secondCol && secondCol !== firstCol) {
      suggestions.push(`Analyze distributions across ${secondCol.name || secondCol.id}`);
    }

    suggestions.push(`Explain p-values & statistical significance`);
    suggestions.push(`Suggest the best statistical method for my variables`);

    return suggestions.slice(0, 4);
  }

  return [
    `Suggest the best statistical method for my dataset`,
    `How does the Assumption Shield verify normality and variance?`,
    `Explain p-values & statistical significance`,
    `Guide me on mapping dependent and independent variables`
  ];
};

export const QuantigenAIChat: React.FC<QuantigenAIChatProps> = ({
  context = {},
  initialMessages = [],
  title = "Quantigen AI Statistical Consultant & Copilot",
  subtitle = "Interactive statistical guidance and next steps",
  onExecuteMethod,
  hideHeader = false,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (initialMessages.length > 0) return initialMessages;
    return [
      {
        id: 'welcome-1',
        role: 'assistant',
        content: `👋 **Hello! I am your Quantigen AI Statistical Consultant & Copilot.**\n\nI am equipped with advanced conversational reasoning to help you navigate your data, interpret exact statistical outputs, verify diagnostic assumptions, and guide your research journey step-by-step.\n\nAsk me anything about your analysis or choose one of the quick follow-up questions below!`,
        suggestedActions: getDynamicSuggestions(context),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ];
  });

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === 'welcome-1' || m.id === 'results-welcome-1'
          ? { ...m, suggestedActions: getDynamicSuggestions(context) }
          : m
      )
    );
  }, [context]);

  const handleSend = async (textToSend?: string) => {
    const question = (textToSend ?? input).trim();
    if (!question || loading) return;

    if (!textToSend) {
      setInput('');
    }
    setError(null);

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      // Prepare history formatted for API
      const historyFormatted = messages.map((m) => ({
        role: m.role,
        content: m.content
      }));

      const res = await api.consultFollowup(question, historyFormatted, context);
      
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: res.message || res.response || "I have analyzed your request based on our statistical knowledge base.",
        suggestedActions: res.suggested_actions || [
          "Explain the effect size for this test",
          "What assumptions were verified?",
          "Suggest my next statistical step",
          "Download reproducible R script"
        ],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || err.message || "Failed to query Quantigen AI Consultant.");
    } finally {
      setLoading(false);
    }
  };

  const formatMarkdownText = (text: string) => {
    return text.split('\n').map((line, idx) => {
      if (!line.trim()) return <div key={idx} className="h-2" />;

      // Blockquotes
      if (line.startsWith('> ')) {
        return (
          <blockquote key={idx} className="border-l-4 border-sky-400 bg-sky-500/10 px-4 py-2 my-2 rounded-r-lg text-sky-200 italic text-sm">
            {renderInlineMarkdown(line.substring(2))}
          </blockquote>
        );
      }

      // Headers
      if (line.startsWith('### ')) {
        return <h4 key={idx} className="text-md font-bold text-sky-300 mt-3 mb-1">{renderInlineMarkdown(line.substring(4))}</h4>;
      }
      if (line.startsWith('## ')) {
        return <h3 key={idx} className="text-lg font-bold text-white mt-3 mb-1">{renderInlineMarkdown(line.substring(3))}</h3>;
      }
      if (line.startsWith('# ')) {
        return <h2 key={idx} className="text-xl font-black text-amber-300 mt-4 mb-2">{renderInlineMarkdown(line.substring(2))}</h2>;
      }

      // Bullet items
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        return (
          <div key={idx} className="flex items-start gap-2.5 my-1.5 pl-2 text-slate-200 text-sm leading-relaxed">
            <span className="text-sky-400 font-bold text-base leading-none mt-0.5">•</span>
            <span className="flex-1">{renderInlineMarkdown(line.trim().substring(2))}</span>
          </div>
        );
      }

      // Numbered items (e.g. 1. )
      const numMatch = line.trim().match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        return (
          <div key={idx} className="flex items-start gap-2.5 my-1.5 pl-2 text-slate-200 text-sm leading-relaxed">
            <span className="text-amber-400 font-bold min-w-[1.2rem]">{numMatch[1]}.</span>
            <span className="flex-1">{renderInlineMarkdown(numMatch[2])}</span>
          </div>
        );
      }

      // Regular paragraph
      return (
        <p key={idx} className="text-slate-200 text-sm leading-relaxed my-1">
          {renderInlineMarkdown(line)}
        </p>
      );
    });
  };

  const renderInlineMarkdown = (content: string) => {
    // Split by bold (**...**) and code (`...`) and math ($...$)
    const parts = content.split(/(\*\*.*?\*\*|`.*?`|\$.*?\$)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-bold text-white bg-white/5 px-1 rounded">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i} className="bg-slate-900 text-sky-300 font-mono text-xs px-1.5 py-0.5 rounded border border-white/10">{part.slice(1, -1)}</code>;
      }
      if (part.startsWith('$') && part.endsWith('$')) {
        return <span key={i} className="text-amber-300 font-serif italic font-semibold px-0.5">{part.slice(1, -1)}</span>;
      }
      return part;
    });
  };

  return (
    <div className={`flex flex-col h-[650px] animate-fade-in ${!hideHeader ? 'glass-panel border border-sky-500/30 rounded-2xl overflow-hidden shadow-2xl shadow-sky-950/40' : ''}`}>
      {!hideHeader && (
        <div className="bg-gradient-to-r from-slate-900 via-sky-950/80 to-slate-900 p-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/20">
              <Sparkles className="w-5 h-5 text-slate-950 animate-pulse" />
            </div>
            <div>
              <h3 className="text-base font-black text-white flex items-center gap-2">
                <span>{title}</span>
                <span className="bg-sky-500/20 text-sky-300 text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border border-sky-500/30">Copilot 4.0</span>
              </h3>
              <p className="text-xs text-slate-400">{subtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-xs font-semibold text-emerald-300">Live Statistical AI</span>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-5 space-y-5 bg-slate-950/60 scrollbar-thin scrollbar-thumb-slate-800">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3.5 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
          >
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md ${
              msg.role === 'user'
                ? 'bg-gradient-to-br from-sky-500 to-blue-600 text-white'
                : 'bg-slate-900 border border-amber-400/30 text-amber-300'
            }`}>
              {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
            </div>

            <div className={`max-w-[82%] rounded-2xl p-4 shadow-xl ${
              msg.role === 'user'
                ? 'bg-gradient-to-r from-sky-600/90 to-blue-600/90 text-white rounded-tr-none border border-sky-400/30'
                : 'bg-slate-900/95 border border-white/10 rounded-tl-none'
            }`}>
              <div className={`flex items-center justify-between gap-4 mb-2 text-xs font-semibold ${
                msg.role === 'user' ? 'text-sky-200' : 'text-amber-300'
              }`}>
                <span>{msg.role === 'user' ? 'You' : 'Quantigen AI Consultant'}</span>
                {msg.timestamp && <span className="text-[10px] opacity-60 font-mono">{msg.timestamp}</span>}
              </div>

              <div className="space-y-1.5 break-words">
                {formatMarkdownText(msg.content)}
              </div>

              {msg.role === 'assistant' && msg.suggestedActions && msg.suggestedActions.length > 0 && (
                <div className="mt-4 pt-3 border-t border-white/10 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-amber-300/90">
                    <Lightbulb className="w-3.5 h-3.5 text-amber-300 animate-bounce" />
                    <span>Suggested Next Questions & Actions (Click to ask directly):</span>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {msg.suggestedActions.map((action, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          if (onExecuteMethod && (action.toLowerCase().includes('run ') || action.toLowerCase().includes('step') || action.toLowerCase().includes('studio'))) {
                            onExecuteMethod(action);
                          } else {
                            handleSend(action);
                          }
                        }}
                        disabled={loading}
                        className="group flex items-center gap-1.5 bg-sky-950/60 hover:bg-sky-500/20 text-sky-200 hover:text-white border border-sky-500/30 hover:border-sky-400 px-3 py-1.5 rounded-xl text-xs font-medium transition-all text-left shadow-sm hover:shadow-sky-500/20"
                      >
                        <span>{action}</span>
                        <ArrowRight className="w-3 h-3 text-sky-400 group-hover:translate-x-0.5 transition-transform" />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-3 animate-pulse">
            <div className="w-9 h-9 rounded-xl bg-slate-900 border border-amber-400/30 text-amber-300 flex items-center justify-center">
              <Sparkles className="w-5 h-5 animate-spin" />
            </div>
            <div className="bg-slate-900/90 border border-white/10 rounded-2xl rounded-tl-none p-4 text-xs font-semibold text-slate-300 flex items-center gap-3">
              <div className="flex space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span>Analyzing statistical properties & generating consultant response...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 sm:p-4 bg-slate-950/90 border-t border-white/10 shadow-2xl flex-shrink-0">
        <ChatInput
          onSend={(message) => handleSend(message)}
          isLoading={loading}
          placeholder="Ask anything about your data... (Shift+Enter for new line)"
        />
      </div>
    </div>
  );
};
