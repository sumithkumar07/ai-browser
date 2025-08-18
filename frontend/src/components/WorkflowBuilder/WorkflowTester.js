import React, { useState } from 'react';

const WorkflowTester = ({ workflow, onClose, onTest, testing }) => {
  const [testResults, setTestResults] = useState(null);
  const [testParameters, setTestParameters] = useState({});

  const handleTest = async () => {
    try {
      const results = await onTest();
      setTestResults(results);
    } catch (error) {
      setTestResults({
        success: false,
        error: error.message
      });
    }
  };

  return (
    <div className="bg-gray-50 border-t border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Workflow Tester</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
      </div>

      <div className="space-y-4">
        {/* Test Parameters */}
        <div>
          <h4 className="font-medium mb-2">Test Parameters</h4>
          <div className="bg-white rounded border p-3">
            <textarea
              placeholder="Enter test data as JSON..."
              value={JSON.stringify(testParameters, null, 2)}
              onChange={(e) => {
                try {
                  setTestParameters(JSON.parse(e.target.value));
                } catch (err) {
                  // Invalid JSON, ignore
                }
              }}
              className="w-full h-20 px-2 py-1 text-sm font-mono"
            />
          </div>
        </div>

        {/* Test Button */}
        <button
          onClick={handleTest}
          disabled={testing}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {testing ? 'Running Test...' : 'Run Test'}
        </button>

        {/* Test Results */}
        {testResults && (
          <div>
            <h4 className="font-medium mb-2">Test Results</h4>
            <div className={`p-3 rounded border ${
              testResults.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
            }`}>
              <pre className="text-sm">
                {JSON.stringify(testResults, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowTester;