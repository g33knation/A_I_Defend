

export default function AskAI() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Ask AI</h1>
          <p className="text-slate-400 mt-1">Query the knowledge base and get instant answers</p>
        </div>
      </div>

      <div className="glass-panel p-8 rounded-xl text-center">
        <div className="w-16 h-16 bg-cyan-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-cyan-500/20">
          <div className="w-8 h-8 bg-cyan-500 rounded-full blur-md"></div>
        </div>
        <h2 className="text-xl font-bold text-white mb-2">How can I assist you?</h2>
        <p className="text-slate-400 max-w-md mx-auto mb-8">
          I can help analyze logs, explain security concepts, or suggest configuration improvements.
        </p>

        <div className="max-w-2xl mx-auto">
          <div className="relative">
            <input
              type="text"
              placeholder="Describe a security incident or ask a question..."
              className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-6 py-4 text-slate-200 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all placeholder:text-slate-600"
            />
            <button className="absolute right-2 top-2 bottom-2 px-6 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-lg transition-colors">
              Ask
            </button>
          </div>

          <div className="mt-8 flex flex-wrap justify-center gap-2">
            {['Analyze recent logs', 'Explain CVE-2024-1234', 'Check firewall rules'].map((suggestion, i) => (
              <button key={i} className="px-4 py-2 rounded-full bg-slate-800/50 hover:bg-slate-800 text-slate-400 hover:text-white text-sm border border-slate-700/50 transition-colors">
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
