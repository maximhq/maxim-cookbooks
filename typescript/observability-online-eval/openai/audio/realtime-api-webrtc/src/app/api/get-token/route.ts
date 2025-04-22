import { NextResponse } from 'next/server'
import OpenAI from 'openai'

// Initialize the OpenAI client with your server-side API key
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY // This should be your full API key stored in server environment
})

export async function GET() {
  try {
    // Create an ephemeral key that expires in 1 hour
    const response = await openai.beta.realtime.sessions.create({      
      model: "gpt-4o-realtime-preview",
      instructions: "You are a helpful voice assistant. Keep responses concise and conversational.",      
      voice: "verse",
    })

    // Return the ephemeral key to the client
    return NextResponse.json(response.client_secret)
  } catch (error) {
    console.error('Error generating ephemeral key:', error)
    return NextResponse.json(
      { error: 'Failed to generate ephemeral key' },
      { status: 500 }
    )
  }
} 