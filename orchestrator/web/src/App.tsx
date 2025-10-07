import React, { useEffect, useState } from 'react'
import { ProjectCard } from './components/ProjectCard'

export default function App() {
  const [projects, setProjects] = useState<any[]>([])

  useEffect(() => {
    fetch('/api/projects')
      .then(r => r.json())
      .then(setProjects)
      .catch(() => setProjects([]))
  }, [])

  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', padding: 16 }}>
      <h1>Project Orchestrator</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
        {projects.map(p => (
          <ProjectCard key={p.id} project={p} />
        ))}
      </div>
    </div>
  )
}

