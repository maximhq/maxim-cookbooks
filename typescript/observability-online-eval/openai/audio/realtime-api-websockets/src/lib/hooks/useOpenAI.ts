import OpenAI from 'openai'
import { useEffect, useState } from 'react'

interface EphemeralKey {
  key: string
  expires_at: string
}

export function useOpenAI() {
  const [client, setClient] = useState<OpenAI | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let timeoutId: NodeJS.Timeout

    const initializeClient = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Fetch ephemeral key from our API
        const response = await fetch('/api/get-token')
        if (!response.ok) {
          throw new Error('Failed to fetch API key')
        }

        const data: EphemeralKey = await response.json()
        
        // Create new OpenAI client with ephemeral key
        const newClient = new OpenAI({
          apiKey: data.key,
          dangerouslyAllowBrowser: true
        })

        setClient(newClient)

        // Calculate when to refresh the key (5 minutes before expiry)
        const expiresAt = new Date(data.expires_at).getTime()
        const now = Date.now()
        const refreshIn = Math.max(0, expiresAt - now - 5 * 60 * 1000) // 5 minutes before expiry

        // Set up refresh timer
        timeoutId = setTimeout(initializeClient, refreshIn)

      } catch (err) {
        console.error('Error initializing OpenAI client:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setIsLoading(false)
      }
    }

    initializeClient()

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
    }
  }, [])

  return { client, error, isLoading }
} 