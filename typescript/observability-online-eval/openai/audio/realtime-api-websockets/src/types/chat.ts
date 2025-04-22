export interface Message {
  id: string
  role: 'user' | 'assistant'
  audio: Blob
  text: string
  isPlaying?: boolean
} 