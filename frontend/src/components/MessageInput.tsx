/**
 * Input de mensagem do chat.
 */

import { useState, useCallback, type KeyboardEvent } from 'react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function MessageInput({
  onSend,
  disabled = false,
  placeholder = 'Digite sua pergunta...',
}: MessageInputProps) {
  const [value, setValue] = useState('');

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;

    onSend(trimmed);
    setValue('');
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  return (
    <div style={styles.container}>
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        style={{
          ...styles.input,
          ...(disabled ? styles.inputDisabled : {}),
        }}
        rows={2}
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
        style={{
          ...styles.button,
          ...(disabled || !value.trim() ? styles.buttonDisabled : {}),
        }}
      >
        Enviar
      </button>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    gap: '0.75rem',
    padding: '1rem',
    background: '#ffffff',
    borderTop: '1px solid #e2e8f0',
  },
  input: {
    flex: 1,
    padding: '0.75rem 1rem',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    fontSize: '0.9375rem',
    fontFamily: 'inherit',
    resize: 'none',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  inputDisabled: {
    background: '#f7fafc',
    cursor: 'not-allowed',
  },
  button: {
    padding: '0.75rem 1.5rem',
    background: '#3182ce',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.9375rem',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'background 0.2s',
  },
  buttonDisabled: {
    background: '#a0aec0',
    cursor: 'not-allowed',
  },
};
