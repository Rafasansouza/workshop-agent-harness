/**
 * Painel de fontes consultadas pelo agente.
 */

import type { FonteConsultada } from '../api/types';

interface SourcesPanelProps {
  fontes: FonteConsultada[] | string[];
  onClose: () => void;
}

export function SourcesPanel({ fontes, onClose }: SourcesPanelProps) {
  // Normaliza fontes para array de objetos
  const fontesNormalizadas: FonteConsultada[] = fontes.map((f, i) => {
    if (typeof f === 'string') {
      return {
        id: `fonte-${i}`,
        colecao: 'desconhecida',
        texto: f,
        score: 0,
        metadata: {},
      };
    }
    return f;
  });

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.panel} onClick={(e) => e.stopPropagation()}>
        <header style={styles.header}>
          <h2 style={styles.title}>Fontes Consultadas</h2>
          <button onClick={onClose} style={styles.closeButton}>
            X
          </button>
        </header>

        <div style={styles.content}>
          {fontesNormalizadas.length === 0 ? (
            <p style={styles.empty}>Nenhuma fonte consultada.</p>
          ) : (
            fontesNormalizadas.map((fonte) => (
              <div key={fonte.id} style={styles.fonte}>
                <div style={styles.fonteHeader}>
                  <span style={styles.colecao}>{fonte.colecao}</span>
                  {fonte.score > 0 && (
                    <span style={styles.score}>
                      Score: {(fonte.score * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                <div style={styles.texto}>{fonte.texto}</div>
                {Object.keys(fonte.metadata).length > 0 && (
                  <div style={styles.metadata}>
                    {fonte.metadata.periodo_referencia && (
                      <span style={styles.tag}>
                        Periodo: {fonte.metadata.periodo_referencia}
                      </span>
                    )}
                    {fonte.metadata.dimensao && (
                      <span style={styles.tag}>
                        Dimensao: {fonte.metadata.dimensao}
                      </span>
                    )}
                    {fonte.metadata.kpi && (
                      <span style={styles.tag}>KPI: {fonte.metadata.kpi}</span>
                    )}
                    {fonte.metadata.fonte && (
                      <span style={styles.tag}>Fonte: {fonte.metadata.fonte}</span>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
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
    width: '500px',
    maxWidth: '90vw',
    background: '#ffffff',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '-4px 0 20px rgba(0, 0, 0, 0.1)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1rem 1.5rem',
    borderBottom: '1px solid #e2e8f0',
    background: '#f7fafc',
  },
  title: {
    margin: 0,
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#2d3748',
  },
  closeButton: {
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'transparent',
    border: '1px solid #e2e8f0',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.875rem',
    color: '#718096',
  },
  content: {
    flex: 1,
    overflowY: 'auto',
    padding: '1rem',
  },
  empty: {
    color: '#718096',
    textAlign: 'center',
    padding: '2rem',
  },
  fonte: {
    padding: '1rem',
    background: '#f7fafc',
    borderRadius: '8px',
    marginBottom: '0.75rem',
    border: '1px solid #e2e8f0',
  },
  fonteHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  colecao: {
    fontSize: '0.75rem',
    color: '#3182ce',
    textTransform: 'uppercase',
    fontWeight: 600,
    letterSpacing: '0.05em',
  },
  score: {
    fontSize: '0.75rem',
    color: '#38a169',
    fontWeight: 500,
  },
  texto: {
    fontSize: '0.875rem',
    color: '#2d3748',
    lineHeight: 1.5,
    whiteSpace: 'pre-wrap',
  },
  metadata: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
    marginTop: '0.75rem',
    paddingTop: '0.75rem',
    borderTop: '1px solid #e2e8f0',
  },
  tag: {
    fontSize: '0.75rem',
    padding: '0.25rem 0.5rem',
    background: '#edf2f7',
    borderRadius: '4px',
    color: '#4a5568',
  },
};
