import React from 'react';

export default function DemoControls({ scenarios, currentScenario, onScenarioChange }) {
  return (
    <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-3 text-center">
      <div className="text-xs font-semibold mb-2">🎯 תרחישי הדגמה</div>
      <div className="flex flex-wrap gap-2 justify-center text-xs">
        {scenarios.map((scenario) => (
          <button
            key={scenario.key}
            onClick={() => onScenarioChange(scenario.key)}
            className={`px-3 py-1 rounded-full transition ${
              currentScenario === scenario.key 
                ? 'bg-white text-indigo-600 font-bold' 
                : 'bg-indigo-500 hover:bg-indigo-400'
            }`}
          >
            {scenario.name}
          </button>
        ))}
      </div>
    </div>
  );
}
