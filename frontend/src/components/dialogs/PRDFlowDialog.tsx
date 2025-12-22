/**
 * PRD Flow Dialog
 * Visual PRD → CICD flow management with state tracking
 */

import React from 'react';
import { X, FileCode, GitBranch, TestTube, Rocket, CheckCircle } from 'lucide-react';

interface PRDFlowDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const PRDFlowDialog: React.FC<PRDFlowDialogProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const flowStages = [
    { id: 'prd', label: 'PRD Input', icon: FileCode, status: 'completed', color: 'green' },
    { id: 'code', label: 'Code Generation', icon: GitBranch, status: 'running', color: 'blue' },
    { id: 'test', label: 'Testing', icon: TestTube, status: 'pending', color: 'yellow' },
    { id: 'deploy', label: 'Deployment', icon: Rocket, status: 'pending', color: 'gray' },
    { id: 'verify', label: 'Verification', icon: CheckCircle, status: 'pending', color: 'gray' },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-700 border-green-300';
      case 'running': return 'bg-blue-100 text-blue-700 border-blue-300 animate-pulse';
      case 'pending': return 'bg-gray-100 text-gray-500 border-gray-300';
      case 'failed': return 'bg-red-100 text-red-700 border-red-300';
      default: return 'bg-gray-100 text-gray-500 border-gray-300';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">PRD → CICD Flow</h2>
            <p className="text-sm text-gray-600 mt-1">
              Visual tracking of PRD implementation through full CICD pipeline
            </p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        <div className="flex-1 p-8 overflow-auto">
          {/* Flow Visualization */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Flow Status</h3>
            <div className="flex items-center justify-between">
              {flowStages.map((stage, index) => {
                const Icon = stage.icon;
                return (
                  <React.Fragment key={stage.id}>
                    <div className="flex flex-col items-center">
                      <div className={`w-16 h-16 rounded-full border-2 flex items-center justify-center mb-2 ${getStatusColor(stage.status)}`}>
                        <Icon className="w-8 h-8" />
                      </div>
                      <span className="text-sm font-medium text-gray-700">{stage.label}</span>
                      <span className={`text-xs mt-1 px-2 py-0.5 rounded-full ${getStatusColor(stage.status)}`}>
                        {stage.status}
                      </span>
                    </div>
                    {index < flowStages.length - 1 && (
                      <div className="flex-1 h-0.5 bg-gray-300 mx-4 mb-12" />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>

          {/* PRD Input Section */}
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Input PRD Requirements</h3>
            <textarea
              placeholder="Enter your Product Requirements Document here..."
              className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            <div className="mt-3 flex items-center justify-between">
              <select className="px-3 py-2 border border-gray-300 rounded-lg">
                <option>Select Project</option>
                <option>Project Alpha</option>
                <option>Project Beta</option>
              </select>
              <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium">
                Start Implementation Flow
              </button>
            </div>
          </div>

          {/* State Details */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Codebase State</h4>
              <div className="text-sm text-gray-600 space-y-1">
                <div className="flex justify-between">
                  <span>Branch:</span>
                  <span className="font-mono text-xs">feature/prd-123</span>
                </div>
                <div className="flex justify-between">
                  <span>Commits:</span>
                  <span className="font-mono text-xs">15</span>
                </div>
                <div className="flex justify-between">
                  <span>Files Changed:</span>
                  <span className="font-mono text-xs">42</span>
                </div>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Verification Status</h4>
              <div className="text-sm text-gray-600 space-y-1">
                <div className="flex justify-between">
                  <span>Tests Passing:</span>
                  <span className="text-green-600 font-medium">85%</span>
                </div>
                <div className="flex justify-between">
                  <span>Coverage:</span>
                  <span className="text-blue-600 font-medium">72%</span>
                </div>
                <div className="flex justify-between">
                  <span>Build Status:</span>
                  <span className="text-yellow-600 font-medium">In Progress</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 flex items-center justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium"
          >
            Close
          </button>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium">
            View Detailed Logs
          </button>
        </div>
      </div>
    </div>
  );
};

export default PRDFlowDialog;

