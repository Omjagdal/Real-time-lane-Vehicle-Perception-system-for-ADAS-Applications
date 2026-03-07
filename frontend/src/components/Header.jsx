import { Car, Activity, AlertTriangle } from 'lucide-react'

const steps = [
    { id: 'upload', label: 'Upload' },
    { id: 'processing', label: 'Processing' },
    { id: 'results', label: 'Results' },
]

export default function Header({ page }) {
    const current = steps.findIndex(s => s.id === page)

    return (
        <header className="sticky top-0 z-50 border-b border-white/5 bg-black/40 backdrop-blur-xl">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-6">

                {/* Logo */}
                <div className="flex items-center gap-3 shrink-0">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
                        <Car size={18} className="text-white" />
                    </div>
                    <div>
                        <span className="font-bold text-white tracking-tight">ADAS</span>
                        <span className="ml-1.5 text-[10px] font-medium uppercase tracking-widest text-cyan-500 border border-cyan-500/40 rounded px-1.5 py-0.5">
                            Perception
                        </span>
                    </div>
                </div>

                {/* Step indicator */}
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

                {/* Status indicator */}
                <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Activity size={12} className="text-emerald-400 animate-pulse" />
                    <span className="hidden sm:inline">API Connected</span>
                </div>

            </div>
        </header>
    )
}
