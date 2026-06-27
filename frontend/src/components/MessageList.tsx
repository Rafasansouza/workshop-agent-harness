/**
 * Lista de mensagens do chat.
 */

import type { Message, DoneEvent } from '../api/types';
import { Report } from './Report';
import { InspectionBar } from './InspectionBar';

interface MessageListProps {
  messages: Message[];
  streamingContent?: string;
  isStreaming?: boolean;
  onInspectFontes?: (metadata: DoneEvent['data']) => void;
  onInspectSql?: (metadata: DoneEvent['data']) => void;
}

export function MessageList({
  messages,
  streamingContent,
  isStreaming,
  onInspectFontes,
  onInspectSql,
}: MessageListProps) {
  return (
    <div style={styles.container}>
      {messages.map((message) => (
        <div
          key={message.id}
          style={{
            ...styles.message,
            ...(message.role === 'user' ? styles.userMessage : styles.assistantMessage),
          }}
        >
          <div style={styles.role}>
            {message.role === 'user' ? 'Voce' : 'Agente'}
          </div>
          {message.role === 'user' ? (
            <div style={styles.userContent}>{message.content}</div>
          ) : (
            <>
              <Report content={message.content} />
              {message.metadata && (
                <InspectionBar
                  fontesCount={message.metadata.fontes_consultadas?.length || 0}
                  sqlCount={message.metadata.sql_executados?.length || 0}
                  onOpenFontes={() => onInspectFontes?.(message.metadata!)}
                  onOpenSql={() => onInspectSql?.(message.metadata!)}
                />
              )}
            </>
          )}
        </div>
      ))}
      {isStreaming && streamingContent && (
        <div style={{ ...styles.message, ...styles.assistantMessage }}>
          <div style={styles.role}>Agente</div>
          <Report content={streamingContent} isStreaming />
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    padding: '1rem',
    overflowY: 'auto',
    flex: 1,
  },
  message: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    maxWidth: '90%',
  },
  userMessage: {
    alignSelf: 'flex-end',
  },
  assistantMessage: {
    alignSelf: 'flex-start',
    width: '100%',
    maxWidth: '100%',
  },
  role: {
    fontSize: '0.75rem',
    color: '#718096',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  userContent: {
    padding: '0.75rem 1rem',
    background: '#3182ce',
    color: 'white',
    borderRadius: '8px',
    borderBottomRightRadius: '2px',
  },
};
