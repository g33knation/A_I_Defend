import { useState } from 'react';
import { useDefenseStore } from '../store/defenseStore';
import Agents from './Agents';
import { MessageSquare, Shield } from 'lucide-react';
import ScanProgressBubble from '../components/ScanProgressBubble';

export default function Chat() {
    const [messages, setMessages] = useState<Array<{ role: string, content: string, scanData?: any }>>([
        { role: 'assistant', content: 'Hello! I am your AI Security Assistant. How can I help you analyze threats or configure defenses today?' }
    ]);
    const [input, setInput] = useState('');
    const [activeTab, setActiveTab] = useState<'chat' | 'agents'>('chat');
    const [isLoading, setIsLoading] = useState(false);
    const { models, selectedModel, setSelectedModel, askAI } = useDefenseStore();

    const handleScanComplete = async (scanId: string, target: string, scanner: string) => {
        // Automatically ask AI to analyze results
        setIsLoading(true);
        try {
            const followUpQuery = `The ${scanner} scan on ${target} (Assignment ID: ${scanId}) is complete. Please analyze the results.`;
            // Add an invisible system message or just directly call the API
            const response = await askAI(followUpQuery, selectedModel);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response
            }]);
        } catch (error) {
            console.error("Auto-analysis failed", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = input;
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await askAI(userMessage, selectedModel);

            // Check for scan marker
            // Format: <<<SCAN_STARTED|id={assignment_id}|target={target}|scanner={scanner_name}>>>
            const scanMarkerRegex = /<<<SCAN_STARTED\|id=([^|]+)\|target=([^|]+)\|scanner=([^>]+)>>>/;
            const match = response.match(scanMarkerRegex);

            if (match) {
                // It's a scan start!
                const [fullMatch, assignmentId, target, scanner] = match;
                // Remove the marker from the text
                const cleanContent = response.replace(fullMatch, '').trim();

                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: cleanContent, // Might be empty if it was just the marker
                    scanData: {
                        assignmentId,
                        target,
                        scanner
                    }
                }]);
            } else {
                // Normal message
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: response
                }]);
            }
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `Error: ${error instanceof Error ? error.message : 'Failed to get response form AI'}`
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col glass-panel rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800/50 bg-slate-900/50 flex justify-between items-center shrink-0">
                <div className="flex items-center gap-4">
                    <div>
                        <h1 className="text-lg font-bold text-white">Security Assistant</h1>
                        <p className="text-slate-400 text-xs">AI-powered threat analysis and support</p>
                    </div>
                    <div className="flex bg-slate-800/50 rounded-lg p-1 border border-slate-700/50">
                        <button
                            onClick={() => setActiveTab('chat')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-2 transition-all ${activeTab === 'chat'
                                ? 'bg-cyan-500/10 text-cyan-400 shadow-sm'
                                : 'text-slate-400 hover:text-slate-200'
                                }`}
                        >
                            <MessageSquare size={14} />
                            Chat
                        </button>
                        <button
                            onClick={() => setActiveTab('agents')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-2 transition-all ${activeTab === 'agents'
                                ? 'bg-cyan-500/10 text-cyan-400 shadow-sm'
                                : 'text-slate-400 hover:text-slate-200'
                                }`}
                        >
                            <Shield size={14} />
                            Agents
                        </button>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Model:</span>
                    <select
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded px-2 py-1 focus:outline-none focus:border-cyan-500/50"
                    >
                        {models.map(model => (
                            <option key={model} value={model}>{model}</option>
                        ))}
                    </select>
                </div>
            </div>

            {activeTab === 'chat' ? (
                <>
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                {msg.content && (
                                    <div className={`max-w-[80%] p-4 rounded-xl mb-2 ${msg.role === 'user'
                                        ? 'bg-cyan-500/10 text-cyan-100 border border-cyan-500/20 rounded-br-none'
                                        : 'bg-slate-800/50 text-slate-200 border border-slate-700/50 rounded-bl-none'
                                        }`}>
                                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                    </div>
                                )}
                                {msg.scanData && (
                                    <ScanProgressBubble
                                        assignmentId={msg.scanData.assignmentId}
                                        target={msg.scanData.target}
                                        scanner={msg.scanData.scanner}
                                        onComplete={(id) => handleScanComplete(id, msg.scanData.target, msg.scanData.scanner)}
                                    />
                                )}
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="bg-slate-800/50 text-slate-400 p-4 rounded-xl rounded-bl-none border border-slate-700/50">
                                    <div className="flex gap-1">
                                        <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                        <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                        <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="p-4 border-t border-slate-800/50 bg-slate-900/30 shrink-0">
                        <form onSubmit={handleSend} className="flex gap-2">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask about threats, logs, or configuration..."
                                disabled={isLoading}
                                className="flex-1 bg-slate-950/50 border border-slate-800 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all placeholder:text-slate-600 disabled:opacity-50"
                            />
                            <button
                                type="submit"
                                disabled={isLoading || !input.trim()}
                                className="px-6 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Send
                            </button>
                        </form>
                    </div>
                </>
            ) : (
                <div className="flex-1 overflow-y-auto p-4">
                    <Agents />
                </div>
            )}
        </div>
    );
}
