'use client'

import { useEffect, useRef, useState } from 'react'
import { EventLog } from './EventLog'
import { SessionControls } from './SessionControls'

export interface RealtimeEvent {
  type: string
  event_id?: string
  timestamp?: string
  item?: {
    type: string
    role: string
    content: Array<{
      type: string
      text: string
    }>
  }
  isProcessing?: boolean
}

export function RealtimeConsole() {
  const [isSessionActive, setIsSessionActive] = useState(false)
  const [events, setEvents] = useState<RealtimeEvent[]>([])
  const [dataChannel, setDataChannel] = useState<RTCDataChannel | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const peerConnection = useRef<RTCPeerConnection | null>(null)
  const audioElement = useRef<HTMLAudioElement | null>(null)
  const mediaStream = useRef<MediaStream | null>(null)
  const audioContext = useRef<AudioContext | null>(null)
  const analyserNode = useRef<AnalyserNode | null>(null)
  const eventListenersSet = useRef(false)
  const messageQueue = useRef<RealtimeEvent[]>([])
  const isDataChannelReady = useRef(false)
  const animationFrame = useRef<number>(null)

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

  const processMessageQueue = () => {
    if (isDataChannelReady.current && dataChannel?.readyState === 'open' && messageQueue.current.length > 0) {
      messageQueue.current.forEach(message => {
        try {
          const messageToSend = { ...message }
          delete messageToSend.timestamp
          delete messageToSend.isProcessing
          
          dataChannel.send(JSON.stringify(messageToSend))
          message.timestamp = new Date().toLocaleTimeString()
          setEvents((prev) => [message, ...prev])
        } catch (e) {
          console.error('Failed to send queued message:', e)
        }
      })
      messageQueue.current = []
    }
  }

  const setupDataChannelListeners = (dc: RTCDataChannel) => {
    const handleMessage = (e: MessageEvent) => {
      try {
        const event = JSON.parse(e.data)
        if (!event.timestamp) {
          event.timestamp = new Date().toLocaleTimeString()
        }
        
        setEvents((prev) => {
          if (event.type === 'response.update' || event.type === 'response.end') {
            const filtered = prev.filter(e => !e.isProcessing)
            return [event, ...filtered]
          }
          return [event, ...prev]
        })
      } catch (error) {
        console.error('Error handling message:', error)
      }
    }

    const handleOpen = () => {
      console.log('Data channel opened with state:', dc.readyState)
      console.log('Data channel reliability:', {
        ordered: dc.ordered,
        maxRetransmits: dc.maxRetransmits,
        protocol: dc.protocol
      })
      isDataChannelReady.current = true
      setIsSessionActive(true)
      setIsConnecting(false)
      setEvents([])
      processMessageQueue()
    }

    const handleError = (error: Event) => {
      const rtcError = error as RTCErrorEvent
      console.error('Data channel error details:', {
        errorType: rtcError.error.errorDetail,
        message: rtcError.error.message,
        receivedState: dc.readyState,
        peerConnectionState: peerConnection.current?.connectionState,
        iceConnectionState: peerConnection.current?.iceConnectionState
      })
      
      setEvents((prev) => [{
        type: 'error',
        event_id: crypto.randomUUID(),
        timestamp: new Date().toLocaleTimeString(),
        item: {
          type: 'error',
          role: 'system',
          content: [{
            type: 'text',
            text: `Connection error: ${rtcError.error.message || 'Unknown error'}`
          }]
        }
      }, ...prev])
    }

    const handleClose = () => {
      console.log('Data channel closed. Final state:', {
        dataChannelState: dc.readyState,
        peerConnectionState: peerConnection.current?.connectionState,
        iceConnectionState: peerConnection.current?.iceConnectionState
      })
      isDataChannelReady.current = false
      stopSession()
    }

    dc.addEventListener('message', handleMessage)
    dc.addEventListener('open', handleOpen)
    dc.addEventListener('error', handleError)
    dc.addEventListener('close', handleClose)

    if (peerConnection.current) {
      peerConnection.current.oniceconnectionstatechange = () => {
        console.log('ICE connection state change:', {
          iceState: peerConnection.current?.iceConnectionState,
          connectionState: peerConnection.current?.connectionState,
          dataChannelState: dc.readyState
        })
        if (peerConnection.current?.iceConnectionState === 'disconnected') {
          console.log('ICE disconnected - stopping session')
          stopSession()
        }
      }
    }

    return () => {
      dc.removeEventListener('message', handleMessage)
      dc.removeEventListener('open', handleOpen)
      dc.removeEventListener('error', handleError)
      dc.removeEventListener('close', handleClose)
    }
  }

  async function startSession() {
    try {
      setIsConnecting(true)
      setEvents([])
      setIsSessionActive(false)
      setIsRecording(false)
      isDataChannelReady.current = false
      messageQueue.current = []

      const tokenResponse = await fetch('/api/get-token')
      if (!tokenResponse.ok) {
        throw new Error(`Failed to get token: ${tokenResponse.status} ${tokenResponse.statusText}`)
      }
      const data = await tokenResponse.json()
      const EPHEMERAL_KEY = data.value

      if (!EPHEMERAL_KEY) {
        throw new Error('No token received from server')
      }

      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' }
        ]
      })

      pc.onconnectionstatechange = () => {
        console.log('Connection state change:', {
          connectionState: pc.connectionState,
          iceConnectionState: pc.iceConnectionState,
          signalingState: pc.signalingState
        })
      }

      audioContext.current = new AudioContext({
        sampleRate: 16000,
        latencyHint: 'interactive'
      })
      
      audioElement.current = document.createElement('audio')
      audioElement.current.autoplay = true

      pc.ontrack = (e) => {
        if (audioElement.current && e.streams[0]) {
          audioElement.current.srcObject = e.streams[0]
        }
      }

      pc.oniceconnectionstatechange = () => {
        console.log('ICE connection state:', pc.iceConnectionState, {
          connectionState: pc.connectionState,
          signalingState: pc.signalingState
        })
        if (pc.iceConnectionState === 'disconnected') {
          stopSession()
        }
      }

      const dc = pc.createDataChannel('oai-events', {
        ordered: true,
        maxRetransmits: 3
      })
      
      setupDataChannelListeners(dc)
      setDataChannel(dc)

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
          const inputData = e.inputBuffer.getChannelData(0)
          const isAudioActive = inputData.some(value => Math.abs(value) > 0.01)
          
          if (isAudioActive) {
            console.log('Audio activity detected', {
              timestamp: new Date().toISOString(),
              peakAmplitude: Math.max(...inputData.map(Math.abs)),
              isRecording,
              dataChannelState: dataChannel?.readyState,
              peerConnectionState: peerConnection.current?.connectionState
            })
          }
        }

        stream.getTracks().forEach(track => {
          if (track.kind === 'audio') {
            console.log('Adding audio track:', {
              trackEnabled: track.enabled,
              trackMuted: track.muted,
              trackReadyState: track.readyState,
              trackSettings: track.getSettings()
            })
            pc.addTrack(track, stream)
          }
        })

      } catch (err) {
        console.error('Error accessing microphone:', err)
        throw new Error('Microphone access denied')
      }

      const offer = await pc.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: false
      })

      await pc.setLocalDescription(offer)

      const baseUrl = 'https://api.openai.com/v1/realtime'
      const model = 'gpt-4o-realtime-preview-2024-12-17'
      
      const sdpResponse = await fetch(`${baseUrl}?model=${model}`, {
        method: 'POST',
        body: offer.sdp,
        headers: {
          Authorization: `Bearer ${EPHEMERAL_KEY}`,
          'Content-Type': 'application/sdp'
        }
      })

      if (!sdpResponse.ok) {
        const error = await sdpResponse.text()
        throw new Error(`OpenAI connection failed (${sdpResponse.status}): ${error}`)
      }

      const answer = {
        type: 'answer',
        sdp: await sdpResponse.text()
      }

      await pc.setRemoteDescription(answer as RTCSessionDescriptionInit)
      peerConnection.current = pc

      setIsRecording(true)
      if (mediaStream.current) {
        mediaStream.current.getTracks().forEach(track => {
          track.enabled = true
          console.log('Initial track state:', {
            trackEnabled: track.enabled,
            trackMuted: track.muted,
            trackReadyState: track.readyState
          })
        })
      }
      
      const startAudioMessage = {
        type: 'audio.start'
      }

      console.log('Sending initial audio start message:', {
        dataChannelState: dc.readyState,
        isDataChannelReady: isDataChannelReady.current
      })

      if (dc.readyState === 'open') {
        sendClientEvent(startAudioMessage)
      } else {
        console.log('Data channel not ready, queueing audio start message')
        messageQueue.current.push(startAudioMessage)
      }

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

    if (dataChannel && isRecording) {
      try {
        sendClientEvent({
          type: 'audio.stop'
        })
      } catch (e) {
        console.error('Error sending audio stop event:', e)
      }
    }

    if (mediaStream.current) {
      mediaStream.current.getTracks().forEach(track => track.stop())
      mediaStream.current = null
    }

    if (audioContext.current) {
      audioContext.current.close()
      audioContext.current = null
    }

    if (peerConnection.current) {
      peerConnection.current.getSenders().forEach((sender) => {
        if (sender.track) {
          sender.track.stop()
        }
      })
      peerConnection.current.close()
    }

    if (dataChannel) {
      dataChannel.close()
    }

    setIsSessionActive(false)
    setIsRecording(false)
    setIsConnecting(false)
    setDataChannel(null)
    peerConnection.current = null
    eventListenersSet.current = false
    isDataChannelReady.current = false
    messageQueue.current = []
  }

  function sendClientEvent(message: RealtimeEvent) {
    if (dataChannel?.readyState === 'open' && isDataChannelReady.current) {
      const timestamp = new Date().toLocaleTimeString()
      message.event_id = message.event_id || crypto.randomUUID()
      
      const messageToSend = { ...message }
      delete messageToSend.timestamp
      delete messageToSend.isProcessing
      
      try {
        dataChannel.send(JSON.stringify(messageToSend))
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
    } else {
      console.log('Queueing message for later delivery')
      messageQueue.current.push(message)
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
          console.log('Disabled audio track:', {
            trackEnabled: track.enabled,
            trackMuted: track.muted,
            trackReadyState: track.readyState
          })
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
          console.log('Enabled audio track:', {
            trackEnabled: track.enabled,
            trackMuted: track.muted,
            trackReadyState: track.readyState
          })
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