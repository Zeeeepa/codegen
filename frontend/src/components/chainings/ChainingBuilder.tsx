import React, { useState } from 'react';
import { Plus, Trash2, Save, Play } from 'lucide-react';
import { ChainConfig, ChainStep, InitialStep } from '../../types';
import { chainTemplates } from '../../templates/chainTemplates';

interface ChainingBuilderProps {
  onSave: (chain: ChainConfig) => void;
  onExecute: (chain: ChainConfig) => void;
  initialChain?: ChainConfig;
}

export const ChainingBuilder: React.FC<ChainingBuilderProps> = ({
  onSave,
  onExecute,
  initialChain
}) => {
  const [chain, setChain] = useState<ChainConfig>(
    initialChain || {
      name: '',
      description: '',
      steps: [],
      contextStrategy: { mode: 'accumulate', maxTokens: 8000 },
      errorHandling: { autoRetry: true, maxGlobalRetries: 3, escalateOnFailure: false, notifyOnError: true }
    }
  );

  const addInitialStep = () => {
    const newStep: InitialStep = {
      type: 'initial',
      prompt: '',
      model: 'Sonnet 4.5',
      taskType: 'implementation',
      description: 'Initial step'
    };
    setChain({ ...chain, steps: [...chain.steps, newStep] });
  };

  const loadTemplate = (templateId: string) => {
    const template = chainTemplates[templateId];
    if (template) {
      setChain({
        ...chain,
        name: template.name,
        description: template.description,
        steps: template.steps
      });
    }
  };

  return (
    <div className="flex flex-col h-full p-6">
      <div className="mb-6">
        <h3 className="text-xl font-bold mb-4">Chaining Builder</h3>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Load Template</label>
          <select
            onChange={(e) => loadTemplate(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg"
          >
            <option value="">Start from scratch</option>
            {Object.values(chainTemplates).map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Chain Name *</label>
            <input
              type="text"
              value={chain.name}
              onChange={(e) => setChain({ ...chain, name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="My Awesome Chain"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description *</label>
            <textarea
              value={chain.description}
              onChange={(e) => setChain({ ...chain, description: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              rows={2}
              placeholder="What does this chain do?"
            />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto mb-6">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium">Steps ({chain.steps.length})</h4>
          <button
            onClick={addInitialStep}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm flex items-center"
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Step
          </button>
        </div>

        {chain.steps.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No steps yet. Add a step or load a template!</p>
          </div>
        ) : (
          <div className="space-y-2">
            {chain.steps.map((step, idx) => (
              <div key={idx} className="p-3 border rounded-lg bg-gray-50">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Step {idx + 1}: {step.type}</span>
                  <button
                    onClick={() => {
                      const newSteps = chain.steps.filter((_, i) => i !== idx);
                      setChain({ ...chain, steps: newSteps });
                    }}
                    className="p-1 hover:bg-red-100 rounded"
                  >
                    <Trash2 className="w-4 h-4 text-red-600" />
                  </button>
                </div>
                <p className="text-xs text-gray-600 mt-1">{step.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex space-x-3">
        <button
          onClick={() => onSave(chain)}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center justify-center"
        >
          <Save className="w-4 h-4 mr-2" />
          Save Chain
        </button>
        <button
          onClick={() => onExecute(chain)}
          className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center justify-center"
        >
          <Play className="w-4 h-4 mr-2" />
          Execute
        </button>
      </div>
    </div>
  );
};

export default ChainingBuilder;
