/**
 * Barra de inspeção — mostra botões para ver fontes e SQL.
 */

interface InspectionBarProps {
  fontesCount: number;
  sqlCount: number;
  onOpenFontes: () => void;
  onOpenSql: () => void;
}

export function InspectionBar({
  fontesCount,
  sqlCount,
  onOpenFontes,
  onOpenSql,
}: InspectionBarProps) {
  if (fontesCount === 0 && sqlCount === 0) {
    return null;
  }

  return (
    <div style={styles.container}>
      <span style={styles.label}>Inspecionar:</span>
      {fontesCount > 0 && (
        <button onClick={onOpenFontes} style={styles.button}>
          <span style={styles.icon}>📚</span>
          <span>{fontesCount} fontes</span>
        </button>
      )}
      {sqlCount > 0 && (
        <button onClick={onOpenSql} style={styles.button}>
          <span style={styles.icon}>🔍</span>
          <span>{sqlCount} queries</span>
        </button>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.5rem 1rem',
    background: '#edf2f7',
    borderRadius: '6px',
    marginTop: '0.75rem',
  },
  label: {
    fontSize: '0.75rem',
    color: '#718096',
    fontWeight: 500,
  },
  button: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
    padding: '0.375rem 0.75rem',
    background: '#ffffff',
    border: '1px solid #e2e8f0',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.8125rem',
    color: '#4a5568',
    transition: 'all 0.2s',
  },
  icon: {
    fontSize: '0.875rem',
  },
};
