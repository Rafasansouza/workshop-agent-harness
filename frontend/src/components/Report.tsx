/**
 * Componente que renderiza o relatório markdown.
 */

import ReactMarkdown from 'react-markdown';

interface ReportProps {
  content: string;
  isStreaming?: boolean;
}

export function Report({ content, isStreaming }: ReportProps) {
  if (!content) return null;

  return (
    <div style={styles.container}>
      <div style={styles.content}>
        <ReactMarkdown>{content}</ReactMarkdown>
        {isStreaming && <span style={styles.cursor}>|</span>}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e2e8f0',
    overflow: 'hidden',
  },
  content: {
    padding: '1.5rem',
    lineHeight: '1.6',
    fontSize: '0.9375rem',
    color: '#2d3748',
  },
  cursor: {
    animation: 'blink 1s step-end infinite',
    color: '#3182ce',
    fontWeight: 'bold',
  },
};
