import { Car, Activity } from 'lucide-react'

const steps = [
    { id: 'upload', label: 'Upload' },
    { id: 'processing', label: 'Processing' },
    { id: 'results', label: 'Results' },
]

export default function Header({ page, onHome }) {
    const current = steps.findIndex(s => s.id === page)
    const isIntro = page === 'intro'

    return (
        <header className="sticky top-0 z-50 border-b border-white/5 bg-black/40 backdrop-blur-xl">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-6">

                {/* Logo — clickable to go home */}
                <button
                    onClick={onHome}
                    className="flex items-center gap-3 shrink-0 group transition-all hover:opacity-80"
                >
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/30 group-hover:shadow-cyan-500/50 transition-all">
                        <Car size={18} className="text-white" />
                    </div>
                    <div>
                        <span className="font-bold text-white tracking-tight">ADAS</span>
                        <span className="ml-1.5 text-[10px] font-medium uppercase tracking-widest text-cyan-500 border border-cyan-500/40 rounded px-1.5 py-0.5">
                            Perception
                        </span>
                    </div>
                </button>

                {/* Step indicator — hidden on intro page */}
                {!isIntro && (
                    <nav className="hidden sm:flex items-center gap-1">
                        {steps.map((step, i) => {
                            const done = i < current
                            const active = i === current
                            return (
                                <div key={step.id} className="flex items-center">
                                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${active ? 'bg-cyan-500/15 text-cyan-400'
                                            : done ? 'text-gray-400'
                                                : 'text-gray-600'
                                        }`}>
                                        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${active ? 'bg-cyan-500 text-white'
                                                : done ? 'bg-white/20 text-white'
                                                    : 'bg-white/5 text-gray-600'
                                            }`}>
                                            {done ? '✓' : i + 1}
                                        </span>
                                        {step.label}
                                    </div>
                                    {i < steps.length - 1 && (
                                        <div className={`w-6 h-px mx-1 ${done ? 'bg-cyan-500/50' : 'bg-white/10'}`} />
                                    )}
                                </div>
                            )
                        })}
                    </nav>
                )}

                {/* Right side */}
                <div className="flex items-center gap-3">
                    {isIntro && (
                        <a
                            href="https://github.com/OmJagdale/Real-time-lane-Vehicle-Perception-system-for-ADAS-Applications"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hidden sm:inline-flex items-center gap-1.5 text-xs text-gray-500 hover:text-cyan-400 transition-colors"
                        >
                            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                            GitHub
                        </a>
                    )}
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Activity size={12} className="text-emerald-400 animate-pulse" />
                        <span className="hidden sm:inline">API Connected</span>
                    </div>
                </div>

            </div>
        </header>
    )
}
