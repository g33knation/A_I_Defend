import { useState } from 'react';

export default function Chat() {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am your AI Security Assistant. How can I help you analyze threats or configure defenses today?' }
    ]);
    const [input, setInput] = useState('');

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        setMessages([...messages, { role: 'user', content: input }]);
        setInput('');

        // Simulate response
        setTimeout(() => {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'I received your query. As a demo, I cannot process real data yet, but I am ready to assist with security configurations.'
            }]);
        }, 1000);
    };

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col glass-panel rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800/50 bg-slate-900/50">
                <h1 className="text-lg font-bold text-white">Security Assistant</h1>
                <p className="text-slate-400 text-xs">AI-powered threat analysis and support</p>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] p-4 rounded-xl ${msg.role === 'user'
                            ? 'bg-cyan-500/10 text-cyan-100 border border-cyan-500/20 rounded-br-none'
                            : 'bg-slate-800/50 text-slate-200 border border-slate-700/50 rounded-bl-none'
                            }`}>
                            <p className="text-sm leading-relaxed">{msg.content}</p>
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-4 border-t border-slate-800/50 bg-slate-900/30">
                <form onSubmit={handleSend} className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about threats, logs, or configuration..."
                        className="flex-1 bg-slate-950/50 border border-slate-800 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all placeholder:text-slate-600"
                    />
                    <button
                        type="submit"
                        className="px-6 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20 rounded-lg font-medium transition-colors"
                    >
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
}
