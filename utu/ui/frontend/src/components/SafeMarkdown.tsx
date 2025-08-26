import React, { useMemo, useState, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import Mermaid from './Mermaid';
import BrokenImagePlaceholder from './BrokenImagePlaceholder';

type CodeProps = React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
};

// Memoized image component to prevent re-renders
const ImageWithErrorHandling = memo(({ src, alt, ...props }: { src?: string; alt?: string; [key: string]: any }) => {
  const [hasError, setHasError] = useState(false);
  
  if (hasError || !src) {
    return <BrokenImagePlaceholder src={src || ''} alt={alt} />;
  }
  
  return (
    <img 
      src={src}
      alt={alt}
      onError={() => setHasError(true)}
      style={{ maxWidth: '100%' }}
      {...props}
    />
  );
});

ImageWithErrorHandling.displayName = 'ImageWithErrorHandling';

// SafeMarkdown component with error boundary and type checking
const SafeMarkdown: React.FC<{ children: React.ReactNode }> = memo(({ children }) => {
  // Function to decode Unicode escape sequences like \u975ePDF
  const decodeUnicodeEscapes = (str: string): string => {
    return str.replace(/\\u([\dA-Fa-f]{4})/g, (_, hex) => {
      return String.fromCharCode(parseInt(hex, 16));
    });
  };

  try {
    // Convert children to string and decode Unicode escapes
    const content = useMemo(() => {
      const str = typeof children === 'string' ? children : String(children);
      return decodeUnicodeEscapes(str);
    }, [children]);
    
    // Return early if content is empty
    if (!content.trim()) return null;
    
    // Extract mermaid code blocks for custom rendering
    // const mermaidChunks = content.match(/```mermaid\n([\s\S]*?)\n```/g) || [];
    // const mermaidContents = mermaidChunks.map(chunk => 
    //   chunk.replace(/^```mermaid\n|```$/g, '').trim()
    // );
    
    const components: Components = {
      // Custom rendering for code blocks
      code({inline, className, children, ...props}: CodeProps) {
        const match = /language-(\w+)/.exec(className || '');
        
        // Handle mermaid code blocks
        if (!inline && match && match[1] === 'mermaid') {
          const content = String(children).replace(/\n$/, '');
          return <Mermaid chart={content} />;
        }
        
        // Default code block rendering
        return (
          <code className={className} {...props}>
            {children}
          </code>
        );
      },
      // Use memoized image component
      img: ImageWithErrorHandling,
      // Custom heading component to avoid conflicts with Mermaid
      h1: ({node, ...props}) => <h1 className="markdown-h1" {...props} />,
      h2: ({node, ...props}) => <h2 className="markdown-h2" {...props} />,
      h3: ({node, ...props}) => <h3 className="markdown-h3" {...props} />,
    };

    return (
      <div className="markdown-content">
        <ReactMarkdown
          remarkPlugins={[remarkMath, remarkGfm]}
          rehypePlugins={[rehypeRaw, rehypeKatex]}
          components={components}
          skipHtml={false}
        >
          {content}
        </ReactMarkdown>
      </div>
    );
  } catch (error) {
    console.error('Error rendering markdown:', error);
    // Fallback to plain text rendering if markdown parsing fails
    return <div className="plain-text">{String(children)}</div>;
  }
});

SafeMarkdown.displayName = 'SafeMarkdown';

export default SafeMarkdown;
