import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Mic, MicOff, Send, Square } from 'lucide-react'
import { useState } from 'react'
import { RealtimeEvent } from './RealtimeConsole'

export interface SessionControlsProps {
  startSession: () => void
  stopSession: () => void
  sendClientEvent: (message: RealtimeEvent) => void
  sendTextMessage: (message: string) => void
  toggleRecording: () => void
  isRecording: boolean
  isConnecting: boolean
  events: RealtimeEvent[]
  isSessionActive: boolean
}

export function SessionControls({
  startSession,
  stopSession,
  sendTextMessage,
  toggleRecording,
  isRecording,
  isConnecting,
  isSessionActive
}: SessionControlsProps) {
  const [message, setMessage] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim()) {
      sendTextMessage(message.trim())
      setMessage('')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        {!isSessionActive ? (
          <Button 
            onClick={startSession} 
            disabled={isConnecting}
          >
            {isConnecting ? 'Connecting...' : 'Start Session'}
          </Button>
        ) : (
          <Button 
            onClick={stopSession} 
            variant="destructive"
          >
            <Square className="w-4 h-4 mr-2" />
            Stop Session
          </Button>
        )}
        {isSessionActive && (
          <Button
            onClick={toggleRecording}
            variant={isRecording ? 'destructive' : 'default'}
            disabled={isConnecting}
          >
            {isRecording ? (
              <>
                <MicOff className="w-4 h-4 mr-2" />
                Stop Recording
              </>
            ) : (
              <>
                <Mic className="w-4 h-4 mr-2" />
                Start Recording
              </>
            )}
          </Button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message..."
          disabled={!isSessionActive}
        />
        <Button type="submit" disabled={!isSessionActive || !message.trim()}>
          <Send className="w-4 h-4" />
        </Button>
      </form>
    </div>
  )
} 