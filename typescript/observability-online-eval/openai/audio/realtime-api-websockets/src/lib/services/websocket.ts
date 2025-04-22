import { RealtimeEvent } from '@/components/realtime/RealtimeConsole'

interface WebSocketServiceConfig {
  onMessage: (event: RealtimeEvent) => void
  onError: (error: Error) => void
  onOpen: () => void
  onClose: () => void
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private config: WebSocketServiceConfig
  private messageQueue: RealtimeEvent[] = []
  private isConnected = false

  constructor(config: WebSocketServiceConfig) {
    this.config = config
  }

  async connect(token: string) {
    try {
      // Connect through the relay server
      const relayUrl = process.env.NEXT_PUBLIC_RELAY_URL || 'ws://localhost:3001'
      const encodedToken = encodeURIComponent(token)
      console.log('token', token)
      this.ws = new WebSocket(`${relayUrl}?token=${encodedToken}`)
      
      this.ws.onopen = () => {
        this.isConnected = true
        this.processMessageQueue()
        this.config.onOpen()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.config.onMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.config.onError(new Error('WebSocket error occurred'))
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event)
        this.isConnected = false
        this.config.onClose()
      }
    } catch (error) {
      console.error('WebSocket connection error:', error)
      this.config.onError(error instanceof Error ? error : new Error('Failed to connect'))
    }
  }

  send(message: RealtimeEvent) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      this.messageQueue.push(message)
    }
  }

  private processMessageQueue() {
    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      while (this.messageQueue.length > 0) {
        const message = this.messageQueue.shift()
        if (message) {
          this.send(message)
        }
      }
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
      this.isConnected = false
      this.messageQueue = []
    }
  }
} 