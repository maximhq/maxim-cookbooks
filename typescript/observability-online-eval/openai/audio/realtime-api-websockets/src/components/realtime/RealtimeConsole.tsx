'use client'

import { WebSocketService } from '@/lib/services/websocket'
import { useEffect, useRef, useState } from 'react'
import { EventLog } from './EventLog'
import { SessionControls } from './SessionControls'

export interface RealtimeEvent {
  type: string
  event_id?: string
  timestamp?: string
  delta?: string
  item?: {
    type: string
    role: string
    content: Array<{
      type: string
      text: string
    }>
  }
  isProcessing?: boolean
  data?: ArrayBuffer
}

export function RealtimeConsole() {
  const [isSessionActive, setIsSessionActive] = useState(false)
  const [events, setEvents] = useState<RealtimeEvent[]>([])
  const [isRecording, setIsRecording] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const mediaStream = useRef<MediaStream | null>(null)
  const audioContext = useRef<AudioContext | null>(null)
  const analyserNode = useRef<AnalyserNode | null>(null)
  const animationFrame = useRef<number | null>(null)
  const wsService = useRef<WebSocketService | null>(null)
  const audioChunks = useRef<Float32Array[]>([])
  const isPlaying = useRef<boolean>(false)

  useEffect(() => {
    return () => {
      if (animationFrame.current) {
        cancelAnimationFrame(animationFrame.current)
      }
    }
  }, [])

  const updateAudioLevel = (timestamp: number) => {
    if (!analyserNode.current || !isRecording) {
      setAudioLevel(0)
      return
    }

    const dataArray = new Uint8Array(analyserNode.current.frequencyBinCount)
    analyserNode.current.getByteFrequencyData(dataArray)
    
    const average = dataArray.reduce((acc, value) => acc + value, 0) / dataArray.length
    const normalizedLevel = average / 255
    
    setAudioLevel(normalizedLevel)
    animationFrame.current = requestAnimationFrame((time) => updateAudioLevel(time))
  }

  const playBufferedAudio = async () => {
    if (!audioContext.current || isPlaying.current) return
    
    isPlaying.current = true
    
    try {
      // Combine all chunks into one large Float32Array
      const totalLength = audioChunks.current.reduce((acc, chunk) => acc + chunk.length, 0)
      const combinedAudio = new Float32Array(totalLength)
      
      let offset = 0
      for (const chunk of audioChunks.current) {
        combinedAudio.set(chunk, offset)
        offset += chunk.length
      }
      
      // Create and fill the audio buffer
      const audioBuffer = audioContext.current.createBuffer(1, combinedAudio.length, 24000)
      audioBuffer.getChannelData(0).set(combinedAudio)
      
      // Create and configure source
      const source = audioContext.current.createBufferSource()
      source.buffer = audioBuffer
      
      // Add a gain node for smooth playback
      const gainNode = audioContext.current.createGain()
      gainNode.gain.setValueAtTime(0, audioContext.current.currentTime)
      gainNode.gain.linearRampToValueAtTime(1, audioContext.current.currentTime + 0.01)
      
      // Connect nodes
      source.connect(gainNode)
      gainNode.connect(audioContext.current.destination)
      
      // Play the audio
      source.start()
      
      // Cleanup after playback
      source.onended = () => {
        source.disconnect()
        gainNode.disconnect()
        isPlaying.current = false
        audioChunks.current = [] // Clear the buffer
      }
    } catch (error) {
      console.error('Error playing buffered audio:', error)
      isPlaying.current = false
      audioChunks.current = [] // Clear the buffer on error
    }
  }

  async function startSession() {
    try {
      setIsConnecting(true)
      setEvents([])
      setIsSessionActive(false)
      setIsRecording(false)

      const tokenResponse = await fetch('/api/get-token')
      if (!tokenResponse.ok) {
        throw new Error(`Failed to get token: ${tokenResponse.status} ${tokenResponse.statusText}`)
      }
      const data = await tokenResponse.json()
      const EPHEMERAL_KEY = data.value

      if (!EPHEMERAL_KEY) {
        throw new Error('No token received from server')
      }

      audioContext.current = new AudioContext({
        sampleRate: 16000,
        latencyHint: 'interactive'
      })

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            channelCount: 1,
            sampleRate: 16000
          }
        })
        mediaStream.current = stream
        
        const analyser = audioContext.current.createAnalyser()
        analyser.fftSize = 2048
        analyser.smoothingTimeConstant = 0.8
        analyserNode.current = analyser

        const source = audioContext.current.createMediaStreamSource(stream)
        source.connect(analyser)
        
        const processor = audioContext.current.createScriptProcessor(1024, 1, 1)
        analyser.connect(processor)
        processor.connect(audioContext.current.destination)

        // Start audio level monitoring
        animationFrame.current = requestAnimationFrame((time) => updateAudioLevel(time))

        processor.onaudioprocess = (e) => {
          if (wsService.current && isRecording) {
            const inputData = e.inputBuffer.getChannelData(0)
            const audioData = new Int16Array(inputData.length)
            
            // Convert Float32 to Int16
            for (let i = 0; i < inputData.length; i++) {
              audioData[i] = Math.max(-32768, Math.min(32767, Math.floor(inputData[i] * 32768)))
            }

            wsService.current.send({
              type: 'audio.data',
              data: audioData.buffer
            })
          }
        }

      } catch (err) {
        console.error('Error accessing microphone:', err)
        throw new Error('Microphone access denied')
      }

      // Initialize WebSocket service
      wsService.current = new WebSocketService({
        onMessage: (event) => {
          if (!event.timestamp) {
            event.timestamp = new Date().toLocaleTimeString()
          }
          console.log('event', event)
          if(event.type === "response.audio.delta") {
            try {
              // Create audio context if not exists
              if (!audioContext.current) {
                audioContext.current = new AudioContext()
              }

              // Decode base64 PCM16 audio data
              const decodedAudio = atob(event.delta || '')
              
              // Convert to ArrayBuffer
              const uint8Array = new Uint8Array(decodedAudio.length)
              for (let i = 0; i < decodedAudio.length; i++) {
                uint8Array[i] = decodedAudio.charCodeAt(i)
              }
              
              // Convert to Int16Array for PCM16 data
              const pcm16Data = new Int16Array(uint8Array.buffer)
              
              // Convert Int16 PCM to Float32 Audio (-32768...32767) to (-1...1)
              const float32Data = new Float32Array(pcm16Data.length)
              for (let i = 0; i < pcm16Data.length; i++) {
                float32Data[i] = pcm16Data[i] / 32768.0
              }

              // Store the chunk
              audioChunks.current.push(float32Data)
              
            } catch (error) {
              console.error('Error processing audio chunk:', error)
            }
          } else if (event.type === "response.audio.done") {
            playBufferedAudio()
          }
          
          setEvents((prev) => {
            if (event.type === 'response.update' || event.type === 'response.end') {
              const filtered = prev.filter(e => !e.isProcessing)
              return [event, ...filtered]
            }
            return [event, ...prev]
          })
        },
        onError: (error) => {
          setEvents((prev) => [{
            type: 'error',
            event_id: crypto.randomUUID(),
            timestamp: new Date().toLocaleTimeString(),
            item: {
              type: 'error',
              role: 'system',
              content: [{
                type: 'text',
                text: `Connection error: ${error.message}`
              }]
            }
          }, ...prev])
          stopSession()
        },
        onOpen: () => {
          setIsSessionActive(true)
          setIsConnecting(false)
          setEvents([])
          sendClientEvent({
            type: 'audio.start'
          })
        },
        onClose: () => {
          stopSession()
        }
      })

      await wsService.current.connect(EPHEMERAL_KEY)
      setIsRecording(true)

    } catch (error) {
      console.error('Session start failed:', error)
      setEvents((prev) => [{
        type: 'error',
        event_id: crypto.randomUUID(),
        timestamp: new Date().toLocaleTimeString(),
        item: {
          type: 'error',
          role: 'system',
          content: [{
            type: 'text',
            text: `Failed to start session: ${error instanceof Error ? error.message : 'Unknown error'}`
          }]
        }
      }, ...prev])
      stopSession()
    }
  }

  function stopSession() {
    if (animationFrame.current) {
      cancelAnimationFrame(animationFrame.current)
    }

    if (wsService.current && isRecording) {
      sendClientEvent({
        type: 'audio.stop'
      })
    }

    if (mediaStream.current) {
      mediaStream.current.getTracks().forEach(track => track.stop())
      mediaStream.current = null
    }

    if (audioContext.current) {
      audioContext.current.close()
      audioContext.current = null
    }

    if (wsService.current) {
      wsService.current.disconnect()
      wsService.current = null
    }

    setIsSessionActive(false)
    setIsRecording(false)
    setIsConnecting(false)
  }

  function sendClientEvent(message: RealtimeEvent) {
    if (wsService.current) {
      const timestamp = new Date().toLocaleTimeString()
      message.event_id = message.event_id || crypto.randomUUID()
      
      try {
        wsService.current.send(message)
        message.timestamp = timestamp
        setEvents((prev) => [message, ...prev])
      } catch (e) {
        console.error('Failed to send message:', e)
        setEvents((prev) => [{
          type: 'error',
          event_id: crypto.randomUUID(),
          timestamp: new Date().toLocaleTimeString(),
          item: {
            type: 'error',
            role: 'system',
            content: [{
              type: 'text',
              text: 'Failed to send message to server'
            }]
          }
        }, ...prev])
      }
    }
  }

  function sendTextMessage(message: string) {
    const event: RealtimeEvent = {
      type: 'conversation.item.create',
      item: {
        type: 'message',
        role: 'user',
        content: [
          {
            type: 'input_text',
            text: message
          }
        ]
      }
    }
    
    sendClientEvent(event)
    sendClientEvent({ 
      type: 'response.create',
      isProcessing: true 
    })
  }

  async function toggleRecording() {
    if (!isSessionActive || isConnecting) return

    if (isRecording) {
      setIsRecording(false)
      if (mediaStream.current) {
        mediaStream.current.getTracks().forEach(track => {
          track.enabled = false
        })
      }
      sendClientEvent({
        type: 'audio.stop'
      })
    } else {
      setIsRecording(true)
      if (mediaStream.current) {
        mediaStream.current.getTracks().forEach(track => {
          track.enabled = true
        })
      }
      sendClientEvent({
        type: 'audio.start'
      })
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <nav className="h-16 flex items-center border-b border-border px-4">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold">Realtime Console</h1>
          {isRecording && (
            <div className="flex items-center gap-2">
              <div 
                className="h-2 bg-green-500 rounded transition-all duration-100" 
                style={{ 
                  width: `${Math.max(20, audioLevel * 100)}px`,
                  opacity: audioLevel > 0.01 ? 1 : 0.5
                }} 
              />
              <span className="text-xs text-gray-500">
                {audioLevel > 0.01 ? 'Audio detected' : 'Waiting for audio...'}
              </span>
            </div>
          )}
        </div>
      </nav>

      <main className="flex-1 flex overflow-hidden">
        <section className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-4">
            <EventLog events={events} />
          </div>
          <div className="h-32 p-4 border-t border-border">
            <SessionControls
              startSession={startSession}
              stopSession={stopSession}
              sendClientEvent={sendClientEvent}
              sendTextMessage={sendTextMessage}
              toggleRecording={toggleRecording}
              isRecording={isRecording}
              isConnecting={isConnecting}
              events={events}
              isSessionActive={isSessionActive}
            />
          </div>
        </section>
      </main>
    </div>
  )
} 