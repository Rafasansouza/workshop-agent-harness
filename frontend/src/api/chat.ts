/**
 * Serviço de chat — consome o endpoint /chat via SSE.
 */

import type { ChatRequest, SSEEvent } from './types';

/**
 * Envia mensagem e processa eventos SSE.
 *
 * @param request - Dados da requisição
 * @param onEvent - Callback chamado para cada evento SSE
 * @param signal - AbortSignal para cancelamento
 */
export async function sendMessage(
  request: ChatRequest,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch('/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Erro ao enviar mensagem: ${response.status}`);
  }

  if (!response.body) {
    throw new Error('Resposta sem corpo');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Processa eventos completos (terminam com \n\n)
    const events = buffer.split('\n\n');
    buffer = events.pop() || '';

    for (const eventStr of events) {
      if (!eventStr.trim()) continue;

      const parsed = parseSSEEvent(eventStr);
      if (parsed) {
        onEvent(parsed);
      }
    }
  }
}

/**
 * Parseia uma string de evento SSE.
 */
function parseSSEEvent(eventStr: string): SSEEvent | null {
  const lines = eventStr.split('\n');
  let eventType = 'message';
  let data = '';

  for (const line of lines) {
    if (line.startsWith('event:')) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith('data:')) {
      data = line.slice(5).trim();
    }
  }

  if (!data) return null;

  try {
    const parsedData = JSON.parse(data);
    return {
      event: eventType as SSEEvent['event'],
      data: parsedData,
    } as SSEEvent;
  } catch {
    console.error('Erro ao parsear evento SSE:', data);
    return null;
  }
}
