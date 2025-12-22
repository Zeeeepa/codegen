import React from 'react';
import SingleViewDashboard from './components/SingleViewDashboard';

// Get credentials from environment variables
const API_KEY = import.meta.env.VITE_CODEGEN_API_KEY || '';
const ORG_ID = import.meta.env.VITE_CODEGEN_ORG_ID || '';

function App() {
  // Validate credentials
  if (!API_KEY || !ORG_ID) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md">
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-red-600"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Configuration Required</h2>
            <p className="text-gray-600 mb-4">
              Please configure your CodeGen API credentials in the .env file:
            </p>
            <div className="bg-gray-50 rounded p-3 text-left font-mono text-sm text-gray-700 mb-4">
              VITE_CODEGEN_API_KEY=your_key
              <br />
              VITE_CODEGEN_ORG_ID=your_org_id
            </div>
            <p className="text-xs text-gray-500">
              Check frontend/.env for configuration details
            </p>
          </div>
        </div>
      </div>
    );
  }

  return <SingleViewDashboard apiKey={API_KEY} orgId={ORG_ID} />;
}

export default App;

