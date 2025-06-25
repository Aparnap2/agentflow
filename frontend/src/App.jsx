import { Routes, Route } from 'react-router-dom'
import StartPage from './pages/StartPage'
import VisionPage from './pages/VisionPage'
import AgentsPage from './pages/AgentsPage'
import OutputsPage from './pages/OutputsPage'
import Navigation from './components/Navigation'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<StartPage />} />
          <Route path="/start" element={<StartPage />} />
          <Route path="/vision" element={<VisionPage />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="/outputs" element={<OutputsPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App