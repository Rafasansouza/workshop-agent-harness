/**
 * Componentes de estados da UI (loading, erro, vazio).
 */

interface LoadingProps {
  node?: string;
  message?: string;
}

export function Loading({ node, message }: LoadingProps) {
  return (
    <div style={styles.container}>
      <div style={styles.spinner} />
      <div style={styles.text}>
        {node && <span style={styles.node}>{node}</span>}
        <span>{message || 'Processando...'}</span>
      </div>
    </div>
  );
}

interface ErrorDisplayProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div style={styles.errorContainer}>
      <div style={styles.errorIcon}>!</div>
      <div style={styles.errorText}>{message}</div>
      {onRetry && (
        <button onClick={onRetry} style={styles.retryButton}>
          Tentar novamente
        </button>
      )}
    </div>
  );
}

export function Empty() {
  return (
    <div style={styles.emptyContainer}>
      <div style={styles.emptyIcon}>?</div>
      <div style={styles.emptyText}>
        Faça uma pergunta para começar a análise
      </div>
      <div style={styles.emptyHint}>
        Ex: "Como melhorar as vendas na região Sul?"
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    padding: '1rem',
    background: '#f0f4f8',
    borderRadius: '8px',
    marginBottom: '1rem',
  },
  spinner: {
    width: '24px',
    height: '24px',
    border: '3px solid #e2e8f0',
    borderTopColor: '#3182ce',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  text: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
  },
  node: {
    fontSize: '0.75rem',
    color: '#718096',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  errorContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '1rem',
    padding: '2rem',
    background: '#fff5f5',
    borderRadius: '8px',
    border: '1px solid #feb2b2',
  },
  errorIcon: {
    width: '48px',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#fc8181',
    color: 'white',
    fontSize: '24px',
    fontWeight: 'bold',
    borderRadius: '50%',
  },
  errorText: {
    color: '#c53030',
    textAlign: 'center',
  },
  retryButton: {
    padding: '0.5rem 1rem',
    background: '#c53030',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.875rem',
  },
  emptyContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '1rem',
    padding: '3rem',
    color: '#718096',
  },
  emptyIcon: {
    width: '64px',
    height: '64px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#e2e8f0',
    color: '#a0aec0',
    fontSize: '32px',
    fontWeight: 'bold',
    borderRadius: '50%',
  },
  emptyText: {
    fontSize: '1.125rem',
    color: '#4a5568',
  },
  emptyHint: {
    fontSize: '0.875rem',
    fontStyle: 'italic',
  },
};
