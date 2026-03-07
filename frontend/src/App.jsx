import { useState } from 'react'
import Header from './components/Header'
import UploadPage from './components/UploadPage'
import ProcessingPage from './components/ProcessingPage'
import ResultsPage from './components/ResultsPage'

// Simple state-machine router: upload → processing → results
export default function App() {
  const [page, setPage] = useState('upload')
  const [jobId, setJobId] = useState(null)
  const [settings, setSettings] = useState({
    conf: 0.4,
    ego_speed: 60,
    device: 'cpu',
    max_frames: 500,
  })

  function handleJobCreated(id) {
    setJobId(id)
    setPage('processing')
  }

  function handleDone() {
    setPage('results')
  }

  function handleReset() {
    setJobId(null)
    setPage('upload')
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header page={page} />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        {page === 'upload' && (
          <UploadPage
            settings={settings}
            setSettings={setSettings}
            onJob={handleJobCreated}
          />
        )}
        {page === 'processing' && jobId && (
          <ProcessingPage jobId={jobId} onDone={handleDone} />
        )}
        {page === 'results' && jobId && (
          <ResultsPage jobId={jobId} onReset={handleReset} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-4 text-center text-xs text-gray-600">
        ADAS Perception System · YOLOv11n · IoU Tracking · FCW · Built with React + FastAPI
      </footer>
    </div>
  )
}
