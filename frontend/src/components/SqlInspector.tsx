/**
 * Inspetor de SQL executado pelo agente.
 */

import type { SqlExecutado } from '../api/types';

interface SqlInspectorProps {
  queries: SqlExecutado[] | string[];
  onClose: () => void;
}

export function SqlInspector({ queries, onClose }: SqlInspectorProps) {
  // Normaliza queries para array de objetos
  const queriesNormalizadas: SqlExecutado[] = queries.map((q) => {
    if (typeof q === 'string') {
      return { query: q };
    }
    return q;
  });

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.panel} onClick={(e) => e.stopPropagation()}>
        <header style={styles.header}>
          <h2 style={styles.title}>SQL Executado</h2>
          <button onClick={onClose} style={styles.closeButton}>
            X
          </button>
        </header>

        <div style={styles.content}>
          {queriesNormalizadas.length === 0 ? (
            <p style={styles.empty}>Nenhuma query executada.</p>
          ) : (
            queriesNormalizadas.map((sql, index) => (
              <div key={index} style={styles.queryCard}>
                <div style={styles.queryHeader}>
                  <span style={styles.queryIndex}>Query #{index + 1}</span>
                  <div style={styles.queryMeta}>
                    {sql.tempo_ms !== undefined && (
                      <span style={styles.tempo}>{sql.tempo_ms}ms</span>
                    )}
                    {sql.linhas !== undefined && (
                      <span style={styles.linhas}>{sql.linhas} linhas</span>
                    )}
                  </div>
                </div>
                <pre style={styles.queryCode}>{formatSql(sql.query)}</pre>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function formatSql(sql: string): string {
  // Formatação básica para melhor legibilidade
  return sql
    .replace(/\b(SELECT|FROM|WHERE|AND|OR|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP BY|ORDER BY|LIMIT|HAVING|WITH|AS)\b/gi, '\n$1')
    .replace(/^\n/, '')
    .trim();
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'flex-end',
    zIndex: 1000,
  },
  panel: {
    width: '600px',
    maxWidth: '90vw',
    background: '#1a202c',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '-4px 0 20px rgba(0, 0, 0, 0.2)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1rem 1.5rem',
    borderBottom: '1px solid #2d3748',
    background: '#2d3748',
  },
  title: {
    margin: 0,
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#ffffff',
  },
  closeButton: {
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'transparent',
    border: '1px solid #4a5568',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.875rem',
    color: '#a0aec0',
  },
  content: {
    flex: 1,
    overflowY: 'auto',
    padding: '1rem',
  },
  empty: {
    color: '#a0aec0',
    textAlign: 'center',
    padding: '2rem',
  },
  queryCard: {
    background: '#2d3748',
    borderRadius: '8px',
    marginBottom: '1rem',
    overflow: 'hidden',
  },
  queryHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.75rem 1rem',
    background: '#4a5568',
  },
  queryIndex: {
    fontSize: '0.75rem',
    color: '#e2e8f0',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  queryMeta: {
    display: 'flex',
    gap: '1rem',
  },
  tempo: {
    fontSize: '0.75rem',
    color: '#68d391',
  },
  linhas: {
    fontSize: '0.75rem',
    color: '#63b3ed',
  },
  queryCode: {
    margin: 0,
    padding: '1rem',
    fontSize: '0.8125rem',
    fontFamily: "'Fira Code', 'Consolas', monospace",
    color: '#e2e8f0',
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    overflowX: 'auto',
  },
};
