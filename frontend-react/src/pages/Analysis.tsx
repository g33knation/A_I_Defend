

import { useState, useRef, useEffect } from 'react';
import { useDefenseStore } from '../store/defenseStore';
import { Send, Bot, User, Loader2, AlertTriangle } from 'lucide-react';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

export default function Analysis() {
    const { selectedModel, askAI } = useDefenseStore();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            role: 'user',
            content: input,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await askAI(input, selectedModel);
            const botMessage: Message = {
                role: 'assistant',
                content: response,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            const errorMessage: Message = {
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your request. Please ensure the model server is running.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="h-[calc(100vh-100px)] flex flex-col gap-4">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">AI Analysis</h1>
                    <p className="text-slate-400 mt-1">Interactive security analysis with {selectedModel}</p>
                </div>
                <div className="glass px-4 py-2 rounded-lg border border-violet-500/20 text-violet-400 text-sm font-mono flex items-center gap-2">
                    <Bot className="w-4 h-4" />
                    Active Model: {selectedModel}
                </div>
            </div>

            <div className="flex-1 glass rounded-xl border border-slate-800/50 flex flex-col overflow-hidden">
                {/* Chat Area */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-slate-500 opacity-50">
                            <Bot className="w-16 h-16 mb-4" />
                            <p className="text-lg">Ready to analyze security data</p>
                            <p className="text-sm">Ask about threats, anomalies, or system status</p>
                        </div>
                    ) : (
                        messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                            >
                                <div className={`
                                    w-8 h-8 rounded-full flex items-center justify-center shrink-0
                                    ${msg.role === 'user' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-violet-500/20 text-violet-400'}
                                `}>
                                    {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                                </div>
                                <div className={`
                                    max-w-[80%] rounded-2xl px-4 py-3 text-sm
                                    ${msg.role === 'user'
                                        ? 'bg-cyan-500/10 text-slate-200 border border-cyan-500/20 rounded-tr-none'
                                        : 'bg-slate-800/50 text-slate-300 border border-slate-700/50 rounded-tl-none'}
                                `}>
                                    <p className="whitespace-pre-wrap">{msg.content}</p>
                                    <span className="text-[10px] opacity-50 mt-1 block">
                                        {msg.timestamp.toLocaleTimeString()}
                                    </span>
                                </div>
                            </div>
                        ))
                    )}
                    {isLoading && (
                        <div className="flex gap-4">
                            <div className="w-8 h-8 rounded-full bg-violet-500/20 text-violet-400 flex items-center justify-center shrink-0">
                                <Bot className="w-4 h-4" />
                            </div>
                            <div className="bg-slate-800/50 rounded-2xl rounded-tl-none px-4 py-3 border border-slate-700/50 flex items-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin text-violet-400" />
                                <span className="text-sm text-slate-400">Analyzing...</span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-slate-800/50 bg-slate-900/30">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="Ask about system security..."
                            className="flex-1 bg-slate-950/50 border border-slate-800 rounded-lg px-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50 placeholder:text-slate-600"
                            disabled={isLoading}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isLoading}
                            className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 hover:bg-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-500">
                        <AlertTriangle className="w-3 h-3" />
                        <span>AI responses may vary based on the selected model ({selectedModel}). Verify critical alerts manually.</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
