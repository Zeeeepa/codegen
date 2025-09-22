import React, { useEffect, useState } from 'react'

export function ProjectCard({ project }: { project: any }) {
  const [repos, setRepos] = useState<any[]>([])

  useEffect(() => {
    // For MVP, fetch all repos and pretend linked
    fetch('/api/repos')
      .then(r => r.json())
      .then(setRepos)
      .catch(() => setRepos([]))
  }, [])

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>{project.name}</h3>
        <button onClick={() => alert('Pin/unpin coming soon')}>
          📌
        </button>
      </div>
      <p style={{ color: '#6b7280' }}>{project.description || 'No description'}</p>
      <div>
        <strong>Repositories</strong>
        <ul>
          {repos.slice(0, 3).map((r) => (
            <li key={r.id}>{r.org}/{r.name}</li>
          ))}
        </ul>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={() => alert('Open Branch Board - soon')}>Open</button>
        <button onClick={() => alert('Start Analysis - soon')}>Analyze</button>
        <button onClick={() => alert('Start Codegen Run - soon')}>Run</button>
      </div>
    </div>
  )
}

