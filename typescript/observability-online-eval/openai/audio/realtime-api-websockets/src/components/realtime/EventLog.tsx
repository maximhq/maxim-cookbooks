import { RealtimeEvent } from './RealtimeConsole'

interface EventLogProps {
  events: RealtimeEvent[]
}

function getEventColor(type: string): string {
  switch (type) {
    case 'error':
      return 'text-red-500'
    case 'response.created':
    case 'response.update':
    case 'response.end':
      return 'text-blue-500'
    case 'conversation.item.created':
      return 'text-green-500'
    case 'audio.start':
    case 'audio.stop':
      return 'text-yellow-500'
    default:
      return 'text-gray-400'
  }
}

export function EventLog({ events }: EventLogProps) {
  return (
    <div className="space-y-2 font-mono">
      {events.map((event, index) => (
        <div 
          key={event.event_id || index}
          className="flex items-start gap-2 font-[var(--font-ibm-plex-mono)]"
        >
          <span className="text-gray-400 min-w-[90px] text-sm">
            {event.timestamp}
          </span>
          <span className={`${getEventColor(event.type)} text-sm`}>
            {event.type}
          </span>
          {event.item && (
            <div className="text-sm text-gray-300 break-all">
              {event.item.role === 'user' ? (
                <span className="text-purple-400">User: </span>
              ) : event.item.role === 'assistant' ? (
                <span className="text-green-400">Assistant: </span>
              ) : null}
              {event.item.content.map((content, i) => (
                <span key={i}>{content.text}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
} 