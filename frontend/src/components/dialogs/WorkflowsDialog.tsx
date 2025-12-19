/**
 * Workflows Dialog
 * Connect chainings with conditional statements from agent responses
 */

import React from 'react';
import { X, Workflow, Plus } from 'lucide-react';

interface WorkflowsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const WorkflowsDialog: React.FC<WorkflowsDialogProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <Workflow className="w-6 h-6 mr-2 text-green-600" />
              Workflows
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Connect chainings with conditional logic and agent response processing
            </p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        <div className="flex-1 p-6 overflow-auto">
          <div className="text-center py-12">
            <Workflow className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Build Your First Workflow</h3>
            <p className="text-gray-600 mb-6">
              Combine chainings into intelligent workflows with conditional branching
            </p>
            <button className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium">
              <Plus className="w-4 h-4 inline mr-2" />
              New Workflow
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowsDialog;

