import { useAuthStore } from '../stores/auth'

export interface ServerMessage {
  type: 'text' | 'tool_call' | 'tool_result' | 'thinking' | 'error' | 'done' | 'session_info' | 'session_list' | 'session_history'
  payload: Record<string, any>
  session_id?: string
  timestamp: string
}

export interface ClientMessage {
  type: 'message' | 'command' | 'resume'
  payload: Record<string, any>
}

type MessageHandler = (message: ServerMessage) => void

class ChatWebSocket {
  private ws: WebSocket | null = null
  private handlers: Set<MessageHandler> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(sessionId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const token = useAuthStore.getState().token
      if (!token) {
        reject(new Error('No auth token'))
        return
      }

      let url = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat?token=${token}`
      if (sessionId) {
        url += `&session_id=${sessionId}`
      }

      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const message: ServerMessage = JSON.parse(event.data)
          this.handlers.forEach(handler => handler(message))
        } catch (e) {
          console.error('Failed to parse message:', e)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        reject(error)
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        
        // Attempt reconnect if not intentional close
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          setTimeout(() => {
            console.log(`Reconnecting... attempt ${this.reconnectAttempts}`)
            this.connect(sessionId)
          }, this.reconnectDelay * this.reconnectAttempts)
        }
      }
    })
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000)
      this.ws = null
    }
    this.handlers.clear()
  }

  send(message: ClientMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocket not connected')
    }
  }

  sendMessage(content: string) {
    this.send({
      type: 'message',
      payload: { content }
    })
  }

  resumeSession(sessionId: string) {
    this.send({
      type: 'resume',
      payload: { session_id: sessionId }
    })
  }

  sendCommand(command: string, args: Record<string, any> = {}) {
    this.send({
      type: 'command',
      payload: { command, ...args }
    })
  }

  onMessage(handler: MessageHandler) {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

export const chatWebSocket = new ChatWebSocket()