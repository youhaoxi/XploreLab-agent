import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';
import BrokenImagePlaceholder from './BrokenImagePlaceholder';

interface MermaidProps {
  chart: string;
}

// Initialize Mermaid once with default config
mermaid.initialize({
  startOnLoad: false, // We'll handle rendering manually
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'Arial, sans-serif',
  themeCSS: `
    .node rect, .node circle, .node polygon {
      stroke: var(--mermaid-node, #4a6cf7) !important;
      fill: var(--mermaid-bg, #ffffff) !important;
    }
    .node text {
      fill: var(--mermaid-text, #213547) !important;
    }
    .edgePath path {
      stroke: var(--mermaid-node, #4a6cf7) !important;
    }
  `,
});

const Mermaid: React.FC<MermaidProps> = React.memo(({ chart }) => {
  const mermaidRef = useRef<HTMLDivElement>(null);
  // const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const element = mermaidRef.current;

    const renderDiagram = async () => {
      if (!element) return;

      // Clear previous diagram and error
      element.innerHTML = '';
      // setError(null);

      try {
        // An empty chart is not a valid diagram, but we can treat it as a blank output.
        if (!chart.trim()) {
          return;
        }

        // First, validate the chart syntax. This throws an error on invalid syntax
        // without rendering the ugly error message to the DOM.
        await mermaid.parse(chart);

        // If parsing succeeds, render the diagram.
        // A unique ID is required for each render.
        const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`;
        const { svg } = await mermaid.render(id, chart);

        if (isMounted) {
          element.innerHTML = svg;
        }
      } catch (err) {
        console.error('Error rendering Mermaid diagram:', err);
        if (isMounted) {
          // Extract a readable error message and display it within our component.
          // const message = err instanceof Error ? err.message : String(err);
          // setError(message);
        }
      }
    };

    renderDiagram();

    return () => {
      isMounted = false;
    };
  }, [chart]);

  return (
    <div className="mermaid-container">
      {/* <div
        ref={mermaidRef}
        className="mermaid"
        style={{ display: error ? 'none' : 'block' }}
      /> */}
      
      <BrokenImagePlaceholder
        src={chart}
        alt="Mermaid Chart"
      />
      
    </div>
  );
});

export default Mermaid;
