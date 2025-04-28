import { Maxim, MaximOpenAIRealtimeEventListener } from '@maximai/maxim-js'
import { RealtimeClient } from '@openai/realtime-api-beta'
import cors from 'cors'
import crypto from 'crypto'
import dotenv from 'dotenv'
import express from 'express'
import { createServer } from 'http'
import path from 'path'
import { fileURLToPath } from 'url'
import { WebSocket, WebSocketServer } from 'ws'

// Get the directory name of the current module
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Load environment variables from the root .env file
dotenv.config({ path: path.resolve(__dirname, '../.env') })


export async function startServer() {
  const app = express()
  const port = process.env.PORT || 3001

  app.use(cors())
  const maxim = new Maxim({
    apiKey: process.env.MAXIM_API_KEY || '',
    baseUrl: 'http://localhost:3002'
  })
  const logger = await maxim.logger({
    id: 'cm5grhygo0002jpz5ohlsej3s'
  })
  if(!logger) {
    throw new Error('Failed to create logger')
  }
  const openAIRealtimeEventListener = new MaximOpenAIRealtimeEventListener(logger);

  const server = createServer(app)
  server.listen(port, () => {
    console.log(`Server listening on port ${port}`)
  })

  const wss = new WebSocketServer({ server })

  wss.on('connection', (ws: WebSocket) => {
    console.log('Client connected')

    const client = new RealtimeClient({ 
      apiKey: process.env.OPENAI_API_KEY || '' 
    })

    // Relay: OpenAI Realtime API Event -> Browser Event
    client.realtime.on('server.*', (event: { type: string; [key: string]: any }) => {
      console.log(`Relaying "${event.type}" to Client`)
      ws.send(JSON.stringify(event))
    })
    // client.realtime.on('server.*', openAIRealtimeEventListener.callback);

    client.realtime.on('close', () => ws.close())

    // Relay: Browser Event -> OpenAI Realtime API Event
    const messageQueue: Buffer[] = []

    ws.on('message', (data: Buffer) => {
      try {
        const event = JSON.parse(data.toString())
        
        // Remove isProcessing field if present as it's not supported
        if (event.isProcessing !== undefined) {
          delete event.isProcessing
        }

        if (!client.isConnected()) {
          messageQueue.push(data)
        } else {
          console.log(`Relaying "${event.type}" to OpenAI:`, event)
          
          // Handle special message types
          if (event.type === 'audio.start') {
            client.realtime.send('audio.start', {
              event_id: event.event_id
            })
          } else if (event.type === 'conversation.item.create') {
            client.realtime.send('conversation.item.create', {
              item: event.item,
              event_id: event.event_id
            })
          } else {
            client.realtime.send(event.type, event)
          }
        }
      } catch (error) {
        console.error('Error processing message:', error)
        ws.send(JSON.stringify({ 
          type: 'error', 
          event_id: crypto.randomUUID(),
          error: {
            type: 'invalid_request_error',
            message: 'Error processing message',
            code: 'processing_error'
          }
        }))
      }
    })

    ws.on('close', () => {
      console.log('Client disconnected')
      client.disconnect()
    })

    ws.on('error', (error: Error) => {
      console.error('WebSocket error:', error)
    })

    // Connect to OpenAI Realtime API
    client.connect().catch((error) => {
      console.error('Error connecting to OpenAI:', error)
      ws.close()
    })
  })

  return server
} 

startServer().catch((error) => {
  console.error('Failed to start server:', error)
  process.exit(1)
})
