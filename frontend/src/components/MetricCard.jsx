const colorMap = {
    cyan: 'from-cyan-500/20 to-cyan-500/5 border-cyan-500/30 text-cyan-400',
    indigo: 'from-indigo-500/20 to-indigo-500/5 border-indigo-500/30 text-indigo-400',
    red: 'from-red-500/20 to-red-500/5 border-red-500/30 text-red-400',
    amber: 'from-amber-500/20 to-amber-500/5 border-amber-500/30 text-amber-400',
}

export default function MetricCard({ icon, label, value, color = 'cyan', unit = '' }) {
    const cls = colorMap[color] || colorMap.cyan
    return (
        <div className={`glass bg-gradient-to-br ${cls} border p-4 space-y-3 animate-slide-up`}>
            <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${cls} border flex items-center justify-center opacity-80`}>
                {icon}
            </div>
            <div>
                <p className="text-2xl font-bold text-white font-mono leading-none">
                    {typeof value === 'number' ? value.toLocaleString() : value}
                    {unit && <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>}
                </p>
                <p className="text-xs text-gray-500 mt-1">{label}</p>
            </div>
        </div>
    )
}
