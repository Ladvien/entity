import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';

interface Pipeline {
  [stage: string]: string[];
}

const defaultPipeline: Pipeline = {
  SETUP: ['LoadConfig', 'InitMemory'],
  DO: ['Reason', 'Plan'],
  DELIVER: ['Respond'],
};

interface DragInfo {
  stage: string;
  index: number;
}

const PluginVisualizer: React.FC = () => {
  const [pipeline, setPipeline] = useState<Pipeline>(defaultPipeline);
  const [dragInfo, setDragInfo] = useState<DragInfo | null>(null);

  const handleDragStart = (stage: string, index: number) => (e: React.DragEvent<HTMLDivElement>) => {
    setDragInfo({ stage, index });
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDrop = (stage: string, index?: number) => (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!dragInfo) return;
    const plugin = pipeline[dragInfo.stage][dragInfo.index];
    const newPipeline: Pipeline = { ...pipeline };
    newPipeline[dragInfo.stage] = newPipeline[dragInfo.stage].filter((_, i) => i !== dragInfo.index);
    if (index === undefined) {
      newPipeline[stage].push(plugin);
    } else {
      newPipeline[stage].splice(index, 0, plugin);
    }
    setPipeline(newPipeline);
    setDragInfo(null);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  return (
    <div className="pipeline">
      {Object.entries(pipeline).map(([stage, plugins]) => (
        <div key={stage} className="stage" onDragOver={handleDragOver} onDrop={handleDrop(stage)}>
          <h3>{stage}</h3>
          {plugins.map((plugin, index) => (
            <div
              key={`${stage}-${plugin}-${index}`}
              className="plugin"
              draggable
              onDragStart={handleDragStart(stage, index)}
              onDrop={handleDrop(stage, index)}
              onDragOver={handleDragOver}
            >
              {plugin}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

export function initVisualizer(elementId: string): void {
  const container = document.getElementById(elementId);
  if (!container) return;
  const root = ReactDOM.createRoot(container);
  root.render(<PluginVisualizer />);
}

initVisualizer('plugin-visualizer');
