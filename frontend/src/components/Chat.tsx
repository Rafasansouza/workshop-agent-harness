/**
 * Container principal do chat.
 */

import { useState, useCallback, useRef } from 'react';
import type { Message, ChatState, SSEEvent, DoneEvent } from '../api/types';
import { sendMessage } from '../api/chat';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Loading, ErrorDisplay, Empty } from './Estados';
import { SourcesPanel } from './SourcesPanel';
import { SqlInspector } from './SqlInspector';

type InspectionPanel = 'none' | 'fontes' | 'sql';

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [state, setState] = useState<ChatState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const [nodeMessage, setNodeMessage] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState('');
  const [threadId, setThreadId] = useState<string | null>(null);
  const [inspectionPanel, setInspectionPanel] = useState<InspectionPanel>('none');
  const [inspectionData, setInspectionData] = useState<DoneEvent['data'] | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleSend = useCallback(
    async (content: string) => {
      // Adiciona mensagem do usuario
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Reset state
      setState('loading');
      setError(null);
      setStreamingContent('');
      setCurrentNode(null);
      setNodeMessage(null);

      // Cria AbortController para cancelamento
      abortControllerRef.current = new AbortController();

      let metadata: DoneEvent['data'] | undefined;
      let reportContent = '';

      try {
        await sendMessage(
          { mensagem: content, thread_id: threadId || undefined },
          (event: SSEEvent) => {
            switch (event.event) {
              case 'status':
                setCurrentNode(event.data.node);
                setNodeMessage(event.data.message);
                break;
              case 'chunk':
                reportContent += event.data.content;
                setStreamingContent(reportContent);
                break;
              case 'done':
                metadata = event.data;
                setThreadId(event.data.thread_id);
                break;
              case 'error':
                throw new Error(event.data.message);
            }
          },
          abortControllerRef.current.signal
        );

        // Adiciona mensagem do assistente
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: reportContent,
          timestamp: new Date(),
          metadata,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setState('success');
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          return;
        }
        const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
        setError(errorMessage);
        setState('error');
      } finally {
        setStreamingContent('');
        setCurrentNode(null);
        setNodeMessage(null);
        abortControllerRef.current = null;
      }
    },
    [threadId]
  );

  const handleRetry = useCallback(() => {
    setState('idle');
    setError(null);
  }, []);

  const handleInspectFontes = useCallback((metadata: DoneEvent['data']) => {
    setInspectionData(metadata);
    setInspectionPanel('fontes');
  }, []);

  const handleInspectSql = useCallback((metadata: DoneEvent['data']) => {
    setInspectionData(metadata);
    setInspectionPanel('sql');
  }, []);

  const handleCloseInspection = useCallback(() => {
    setInspectionPanel('none');
    setInspectionData(null);
  }, []);

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Agente Analitico de Vendas</h1>
        {threadId && (
          <span style={styles.threadId}>Thread: {threadId.slice(0, 8)}...</span>
        )}
      </header>

      <main style={styles.main}>
        {messages.length === 0 && state === 'idle' ? (
          <Empty />
        ) : (
          <MessageList
            messages={messages}
            streamingContent={streamingContent}
            isStreaming={state === 'loading' && !!streamingContent}
            onInspectFontes={handleInspectFontes}
            onInspectSql={handleInspectSql}
          />
        )}

        {state === 'loading' && !streamingContent && (
          <Loading node={currentNode || undefined} message={nodeMessage || undefined} />
        )}

        {state === 'error' && error && (
          <ErrorDisplay message={error} onRetry={handleRetry} />
        )}
      </main>

      <footer style={styles.footer}>
        <MessageInput
          onSend={handleSend}
          disabled={state === 'loading'}
          placeholder={
            state === 'loading'
              ? 'Aguarde o processamento...'
              : 'Digite sua pergunta sobre vendas...'
          }
        />
      </footer>

      {inspectionPanel === 'fontes' && inspectionData && (
        <SourcesPanel
          fontes={inspectionData.fontes_consultadas}
          onClose={handleCloseInspection}
        />
      )}

      {inspectionPanel === 'sql' && inspectionData && (
        <SqlInspector
          queries={inspectionData.sql_executados}
          onClose={handleCloseInspection}
        />
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: '#f7fafc',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1rem 1.5rem',
    background: '#2d3748',
    color: 'white',
  },
  title: {
    margin: 0,
    fontSize: '1.25rem',
    fontWeight: 600,
  },
  threadId: {
    fontSize: '0.75rem',
    color: '#a0aec0',
    fontFamily: 'monospace',
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    padding: '1rem',
  },
  footer: {
    background: '#ffffff',
    borderTop: '1px solid #e2e8f0',
  },
};
