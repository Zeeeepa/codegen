import { FC } from 'react';
import VisualFlowEditor from './components/VisualFlowEditor';

const App: FC = () => {
  return (
    <div className="w-full h-full bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">
          CodeGen Tree-of-Thoughts Visual Orchestrator
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          Build, orchestrate, and execute AI agent workflows with intelligent multi-path exploration
        </p>
      </header>
      
      <main className="w-full h-[calc(100%-80px)]">
        <VisualFlowEditor />
      </main>
    </div>
  );
};

export default App;

