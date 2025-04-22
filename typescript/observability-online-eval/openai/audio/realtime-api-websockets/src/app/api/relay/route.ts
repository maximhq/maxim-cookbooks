import { NextRequest } from 'next/server'
import { WebSocket } from 'ws'

export const runtime = 'edge'

export async function GET(req: NextRequest) {
  const upgradeHeader = req.headers.get('upgrade')
  if (upgradeHeader !== 'websocket') {
    return new Response('Expected Upgrade: websocket', { status: 426 })
  }

  try {
    const token = req.nextUrl.searchParams.get('token')
    if (!token) {
      return new Response('Missing token', { status: 400 })
    }

    const webSocketPair = new WebSocketPair()
    const [client, server] = Object.values(webSocketPair)

    // Connect to OpenAI's WebSocket server
    const openaiSocket = new WebSocket('wss://api.openai.com/v1/realtime', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    // Forward messages from client to OpenAI
    server.addEventListener('message', (event: MessageEvent) => {
      if (openaiSocket.readyState === WebSocket.OPEN) {
        openaiSocket.send(event.data)
      }
    })

    // Forward messages from OpenAI to client
    openaiSocket.addEventListener('message', (event: MessageEvent) => {
      if (server.readyState === WebSocket.OPEN) {
        server.send(event.data)
      }
    })

    // Handle closures
    server.addEventListener('close', () => {
      if (openaiSocket.readyState === WebSocket.OPEN) {
        openaiSocket.close()
      }
    })

    openaiSocket.addEventListener('close', () => {
      if (server.readyState === WebSocket.OPEN) {
        server.close()
      }
    })

    // Handle errors
    server.addEventListener('error', (event: Event) => {
      console.error('Client WebSocket error:', event)
      if (openaiSocket.readyState === WebSocket.OPEN) {
        openaiSocket.close()
      }
    })

    openaiSocket.addEventListener('error', (event: Event) => {
      console.error('OpenAI WebSocket error:', event)
      if (server.readyState === WebSocket.OPEN) {
        server.close()
      }
    })

    server.accept()

    return new Response(null, {
      status: 101,
      webSocket: client,
    })
  } catch (error) {
    console.error('WebSocket setup error:', error)
    return new Response('WebSocket setup failed', { status: 500 })
  }
} 