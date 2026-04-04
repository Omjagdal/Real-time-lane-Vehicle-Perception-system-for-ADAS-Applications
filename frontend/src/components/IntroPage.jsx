import {
  ChevronRight, Car, Eye, Gauge, Shield, Radar, Zap,
  Cpu, GitBranch, Timer, Ruler, Activity, AlertTriangle,
  Github, Linkedin, Mail
} from 'lucide-react'

const features = [
  {
    icon: <Eye size={22} />,
    title: 'Lane Detection',
    desc: 'Canny edge + Hough Transform with 8-frame temporal smoothing for stable lane lines.',
    color: 'cyan',
  },
  {
    icon: <Car size={22} />,
    title: 'Vehicle Detection',
    desc: 'YOLOv11n real-time inference — cars, trucks, buses, motorcycles at 0.4 confidence.',
    color: 'indigo',
  },
  {
    icon: <GitBranch size={22} />,
    title: 'Multi-Object Tracking',
    desc: 'IoU-based Hungarian assignment with persistent IDs across frames.',
    color: 'violet',
  },
  {
    icon: <Ruler size={22} />,
    title: 'Distance Estimation',
    desc: 'Pinhole camera model with perspective correction. Range: 1–200 m.',
    color: 'emerald',
  },
  {
    icon: <Gauge size={22} />,
    title: 'Speed Estimation',
    desc: 'Frame-to-frame pixel displacement with EMA smoothing (α = 0.4).',
    color: 'amber',
  },
  {
    icon: <Shield size={22} />,
    title: 'Collision Warning',
    desc: 'TTC-based 3-tier FCW: SAFE → CAUTION → BRAKE with real-time alerts.',
    color: 'red',
  },
]

const colorClasses = {
  cyan: 'from-cyan-500/20 to-cyan-500/5 border-cyan-500/30 text-cyan-400',
  indigo: 'from-indigo-500/20 to-indigo-500/5 border-indigo-500/30 text-indigo-400',
  violet: 'from-violet-500/20 to-violet-500/5 border-violet-500/30 text-violet-400',
  emerald: 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/30 text-emerald-400',
  amber: 'from-amber-500/20 to-amber-500/5 border-amber-500/30 text-amber-400',
  red: 'from-red-500/20 to-red-500/5 border-red-500/30 text-red-400',
}

const pipelineSteps = [
  { label: 'Input Video', icon: '🎥', sub: 'MP4 / AVI / MOV' },
  { label: 'Preprocessing', icon: '⚙️', sub: '1280×720 · Normalize' },
  { label: 'Detection', icon: '🔍', sub: 'YOLOv11n + Hough' },
  { label: 'Tracking', icon: '🆔', sub: 'IoU + Hungarian' },
  { label: 'Estimation', icon: '📏', sub: 'Distance + Speed' },
  { label: 'FCW', icon: '⚠️', sub: 'TTC Alerts' },
  { label: 'Output', icon: '🎬', sub: 'Annotated Video' },
]

const techStack = [
  { name: 'Python', version: '3.11+', icon: '🐍' },
  { name: 'React', version: '18+', icon: '⚛️' },
  { name: 'FastAPI', version: '0.135+', icon: '⚡' },
  { name: 'PyTorch', version: '2.1+', icon: '🔥' },
  { name: 'OpenCV', version: '4.8+', icon: '👁️' },
  { name: 'YOLOv11n', version: 'Ultralytics', icon: '🎯' },
  { name: 'SciPy', version: 'Hungarian', icon: '🧮' },
  { name: 'Vite', version: 'SSE Stream', icon: '⚡' },
]

const metrics = [
  { label: 'Vehicle mAP', value: '55–65%', sub: 'YOLOv11n filtered' },
  { label: 'Tracking MOTA', value: '50–65%', sub: 'IoU-based tracker' },
  { label: 'Lane Detection', value: '70–80%', sub: 'Highway accuracy' },
  { label: 'GPU FPS', value: '15–25', sub: '1280×720 frames' },
]

export default function IntroPage({ onStart }) {
  return (
    <div className="animate-fade-in space-y-16 pb-12">

      {/* ── Hero Section ────────────────────────────────────── */}
      <section className="relative text-center pt-8 md:pt-14">
        {/* Background glow effects */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-cyan-500/8 blur-[120px]" />
          <div className="absolute top-20 left-1/4 w-[400px] h-[400px] rounded-full bg-indigo-500/6 blur-[100px]" />
        </div>

        <div className="relative z-10 space-y-6">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium">
            <Radar size={13} className="animate-pulse" />
            Real-Time Perception Pipeline
          </div>

          {/* Title */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1]">
            <span className="text-white">Advanced Driver</span>
            <br />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
              Assistance System
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
            A complete real-time perception pipeline for autonomous driving —
            from raw dashcam footage to actionable safety alerts, powered by
            deep learning and classical computer vision.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
            <button onClick={onStart} className="btn-primary px-8 py-4 text-base">
              <Zap size={18} />
              Launch Pipeline
              <ChevronRight size={16} />
            </button>
            <a
              href="https://github.com/OmJagdale/Real-time-lane-Vehicle-Perception-system-for-ADAS-Applications"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-outline px-6 py-3.5 text-base"
            >
              <Github size={16} />
              View on GitHub
            </a>
          </div>

          {/* Quick stats row */}
          <div className="flex flex-wrap justify-center gap-6 pt-6">
            {[
              { val: '6', label: 'CV Modules' },
              { val: 'YOLOv11n', label: 'Detection' },
              { val: 'Real-Time', label: 'Processing' },
              { val: '3-Tier', label: 'FCW Alerts' },
            ].map(s => (
              <div key={s.label} className="text-center">
                <p className="text-lg font-bold text-white font-mono">{s.val}</p>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pipeline Architecture ────────────────────────────── */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-bold text-white">Processing Pipeline</h2>
          <p className="text-gray-500 text-sm">End-to-end perception from raw video to annotated output</p>
        </div>

        <div className="glass p-6 md:p-8 overflow-x-auto">
          <div className="flex items-center justify-between min-w-[700px] gap-1">
            {pipelineSteps.map((step, i) => (
              <div key={step.label} className="flex items-center">
                <div className="flex flex-col items-center text-center group">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-white/10 to-white/5 border border-white/10 flex items-center justify-center text-2xl group-hover:border-cyan-500/40 group-hover:shadow-lg group-hover:shadow-cyan-500/10 transition-all duration-300 group-hover:scale-110">
                    {step.icon}
                  </div>
                  <p className="text-xs font-semibold text-gray-300 mt-2.5">{step.label}</p>
                  <p className="text-[10px] text-gray-600 mt-0.5">{step.sub}</p>
                </div>
                {i < pipelineSteps.length - 1 && (
                  <div className="flex items-center mx-2 mt-[-20px]">
                    <div className="w-8 md:w-12 h-px bg-gradient-to-r from-cyan-500/40 to-indigo-500/40" />
                    <ChevronRight size={12} className="text-cyan-500/50 -ml-1" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Feature Cards ───────────────────────────────────── */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-bold text-white">Core Modules</h2>
          <p className="text-gray-500 text-sm">Six tightly integrated perception components</p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f, i) => (
            <div
              key={f.title}
              className={`glass bg-gradient-to-br ${colorClasses[f.color]} border p-5 space-y-3 hover:scale-[1.02] transition-all duration-300 cursor-default`}
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colorClasses[f.color]} border flex items-center justify-center`}>
                {f.icon}
              </div>
              <h3 className="font-semibold text-white text-sm">{f.title}</h3>
              <p className="text-xs text-gray-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── FCW Alert Demo ──────────────────────────────────── */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-bold text-white">Forward Collision Warning</h2>
          <p className="text-gray-500 text-sm">Three-tier Time-To-Collision based alert system</p>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          {/* SAFE */}
          <div className="glass border border-emerald-500/20 bg-emerald-500/5 p-6 text-center space-y-3 hover:border-emerald-500/40 transition-all">
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center mx-auto">
              <Shield size={24} className="text-emerald-400" />
            </div>
            <h3 className="text-emerald-400 font-bold text-lg">✅ SAFE</h3>
            <p className="text-sm text-gray-400">TTC ≥ 3.0 seconds</p>
            <p className="text-sm text-gray-400">Distance ≥ 20 metres</p>
            <div className="text-xs text-gray-600 pt-1">Maintain current speed</div>
          </div>

          {/* CAUTION */}
          <div className="glass border border-amber-500/20 bg-amber-500/5 p-6 text-center space-y-3 hover:border-amber-500/40 transition-all">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center mx-auto">
              <AlertTriangle size={24} className="text-amber-400" />
            </div>
            <h3 className="text-amber-400 font-bold text-lg">⚠️ CAUTION</h3>
            <p className="text-sm text-gray-400">TTC &lt; 3.0 seconds</p>
            <p className="text-sm text-gray-400">Distance ≤ 20 metres</p>
            <div className="text-xs text-gray-600 pt-1">Prepare to decelerate</div>
          </div>

          {/* BRAKE */}
          <div className="glass border border-red-500/20 bg-red-500/5 p-6 text-center space-y-3 hover:border-red-500/40 transition-all">
            <div className="w-14 h-14 rounded-2xl bg-red-500/15 border border-red-500/30 flex items-center justify-center mx-auto animate-pulse-slow">
              <AlertTriangle size={24} className="text-red-400" />
            </div>
            <h3 className="text-red-400 font-bold text-lg">🛑 BRAKE!</h3>
            <p className="text-sm text-gray-400">TTC &lt; 1.5 seconds</p>
            <p className="text-sm text-gray-400">Distance ≤ 10 metres</p>
            <div className="text-xs text-gray-600 pt-1">Immediate braking required</div>
          </div>
        </div>

        {/* TTC formula */}
        <div className="glass p-4 text-center">
          <p className="text-xs text-gray-500 mb-1">TTC Formula</p>
          <p className="font-mono text-sm text-cyan-400">
            TTC = Distance / (Ego_Speed − Vehicle_Speed)
          </p>
        </div>
      </section>

      {/* ── Performance Metrics ──────────────────────────────── */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-bold text-white">Performance Metrics</h2>
          <p className="text-gray-500 text-sm">Benchmarked on real-world dashcam footage</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map(m => (
            <div key={m.label} className="glass p-5 text-center space-y-2 hover:border-cyan-500/30 transition-all">
              <p className="text-2xl md:text-3xl font-bold font-mono bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">
                {m.value}
              </p>
              <p className="text-sm font-semibold text-gray-300">{m.label}</p>
              <p className="text-[11px] text-gray-600">{m.sub}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Tech Stack ───────────────────────────────────────── */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-bold text-white">Technology Stack</h2>
          <p className="text-gray-500 text-sm">Built with industry-standard tools</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {techStack.map(t => (
            <div key={t.name} className="glass p-4 flex items-center gap-3 hover:border-white/20 transition-all group cursor-default">
              <span className="text-2xl group-hover:scale-110 transition-transform">{t.icon}</span>
              <div>
                <p className="text-sm font-semibold text-white">{t.name}</p>
                <p className="text-[10px] text-gray-500">{t.version}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Algorithm Highlight ──────────────────────────────── */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-bold text-white">How It Works</h2>
          <p className="text-gray-500 text-sm">Key algorithms powering the pipeline</p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {/* Distance */}
          <div className="glass p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Ruler size={16} className="text-emerald-400" />
              <h3 className="text-sm font-semibold text-white">Pinhole Camera Distance</h3>
            </div>
            <div className="bg-black/30 rounded-lg p-3 font-mono text-xs text-cyan-300 overflow-x-auto">
              <p>Distance = (Real_Width × Focal_Length) / Pixel_Width</p>
              <p className="text-gray-600 mt-1">// Focal Length: 850px (1280×720)</p>
              <p className="text-gray-600">// Car: 1.8m | Bus: 2.5m | Truck: 2.4m</p>
            </div>
          </div>

          {/* Speed */}
          <div className="glass p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Gauge size={16} className="text-amber-400" />
              <h3 className="text-sm font-semibold text-white">EMA Speed Estimation</h3>
            </div>
            <div className="bg-black/30 rounded-lg p-3 font-mono text-xs text-cyan-300 overflow-x-auto">
              <p>pixel_disp = √((x₂-x₁)² + (y₂-y₁)²)</p>
              <p>speed_kmh = (pixel_disp / scale) × FPS × 3.6</p>
              <p className="text-gray-600 mt-1">// EMA smoothing: α = 0.4</p>
            </div>
          </div>

          {/* Detection */}
          <div className="glass p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Eye size={16} className="text-indigo-400" />
              <h3 className="text-sm font-semibold text-white">YOLOv11n Detection</h3>
            </div>
            <div className="bg-black/30 rounded-lg p-3 font-mono text-xs text-cyan-300 overflow-x-auto">
              <p>COCO Classes: [2: car, 3: moto, 5: bus, 7: truck]</p>
              <p>Conf: 0.4 | NMS IoU: 0.45</p>
              <p className="text-gray-600 mt-1">// ~5.8 MB nano model · GPU: 1.5ms/frame</p>
            </div>
          </div>

          {/* Tracking */}
          <div className="glass p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Activity size={16} className="text-violet-400" />
              <h3 className="text-sm font-semibold text-white">Hungarian IoU Tracking</h3>
            </div>
            <div className="bg-black/30 rounded-lg p-3 font-mono text-xs text-cyan-300 overflow-x-auto">
              <p>cost[i][j] = 1.0 - IoU(track_i, det_j)</p>
              <p>assignment = linear_sum_assignment(cost)</p>
              <p className="text-gray-600 mt-1">// IoU ≥ 0.30 | Max age: 5 | Min hits: 2</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA + Author ─────────────────────────────────────── */}
      <section className="text-center space-y-8 pt-4">
        {/* Final CTA */}
        <div className="glass p-8 md:p-12 space-y-4 border border-cyan-500/10 bg-gradient-to-br from-cyan-500/5 to-indigo-500/5">
          <h2 className="text-2xl md:text-3xl font-bold text-white">Ready to Analyze?</h2>
          <p className="text-gray-400 max-w-lg mx-auto text-sm">
            Upload your dashcam footage and watch the ADAS pipeline detect lanes,
            track vehicles, estimate distances, and generate collision warnings in real time.
          </p>
          <button onClick={onStart} className="btn-primary px-10 py-4 text-base mt-2">
            <Zap size={18} />
            Start Processing
            <ChevronRight size={16} />
          </button>
        </div>

        {/* Author */}
        <div className="space-y-3">
          <p className="text-sm text-gray-500">Computer Vision & AI · ADAS · Deep Learning · Edge AI</p>
          <div className="flex justify-center gap-3 pt-1">
            <a href="https://linkedin.com/in/omjagdale" target="_blank" rel="noopener noreferrer"
              className="w-9 h-9 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 hover:text-cyan-400 hover:border-cyan-500/40 transition-all">
              <Linkedin size={15} />
            </a>
            <a href="https://github.com/OmJagdale" target="_blank" rel="noopener noreferrer"
              className="w-9 h-9 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 hover:text-cyan-400 hover:border-cyan-500/40 transition-all">
              <Github size={15} />
            </a>
            <a href="mailto:omjagdale.ai@gmail.com"
              className="w-9 h-9 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 hover:text-cyan-400 hover:border-cyan-500/40 transition-all">
              <Mail size={15} />
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}
