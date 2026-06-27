/**
 * Tipos do contrato da API de chat.
 */

/** Request para o endpoint /chat */
export interface ChatRequest {
  mensagem: string;
  thread_id?: string;
}

/** Evento SSE de status (qual nó está executando) */
export interface StatusEvent {
  event: 'status';
  data: {
    node: string;
    message: string;
  };
}

/** Evento SSE de chunk (pedaço do relatório) */
export interface ChunkEvent {
  event: 'chunk';
  data: {
    content: string;
  };
}

/** Fonte consultada pelo agente */
export interface FonteConsultada {
  id: string;
  colecao: string;
  texto: string;
  score: number;
  metadata: {
    periodo_referencia?: string;
    dimensao?: string;
    kpi?: string;
    fonte?: string;
  };
}

/** SQL executado pelo agente */
export interface SqlExecutado {
  query: string;
  tempo_ms?: number;
  linhas?: number;
}

/** Evento SSE done (fim da execução) */
export interface DoneEvent {
  event: 'done';
  data: {
    thread_id: string;
    premissas: string[];
    kpis_fracos: KpiFraco[];
    sql_executados: SqlExecutado[] | string[];
    fontes_consultadas: FonteConsultada[] | string[];
  };
}

/** Evento SSE de erro */
export interface ErrorEvent {
  event: 'error';
  data: {
    message: string;
  };
}

/** KPI abaixo da meta */
export interface KpiFraco {
  kpi: string;
  dimensao: string;
  valor_atual: number;
  valor_meta: number;
  gap_percentual: number;
}

/** União de todos os eventos SSE */
export type SSEEvent = StatusEvent | ChunkEvent | DoneEvent | ErrorEvent;

/** Mensagem no histórico do chat */
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: DoneEvent['data'];
}

/** Estados possíveis do chat */
export type ChatState = 'idle' | 'loading' | 'error' | 'success';
