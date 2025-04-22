import { cn } from '@/lib/utils'
import { RealtimeEvent } from './RealtimeConsole'

interface EventLogProps {
  events: RealtimeEvent[]
}

function WaveAnimation() {
  return (
    <div className="flex gap-1 h-4 items-end">
      {[...Array(3)].map((_, i) => (
        <div
          key={i}
          className="w-1 bg-primary animate-wave"
          style={{
            height: '30%',
            animationDelay: `${i * 0.15}s`
          }}
        />
      ))}
    </div>
  )
}

export function EventLog({ events }: EventLogProps) {
  return (
    <div className="space-y-4">
      {events.map((event) => (
        <div
          key={event.event_id}
          className={cn(
            "p-4 rounded-lg border border-border",
            event.isProcessing ? "bg-muted" : "bg-card"
          )}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">
              {event.timestamp}
            </span>
            <span className="text-sm font-mono text-muted-foreground">
              {event.type}
            </span>
          </div>
          
          {event.item && (
            <div className="mt-2">
              <div className="text-sm font-medium">
                {event.item.role === 'user' ? 'User' : 'Assistant'}
              </div>
              {event.item.content.map((content, i) => (
                <div key={i} className="mt-1 text-sm">
                  {content.text}
                </div>
              ))}
            </div>
          )}
          
          {event.isProcessing && (
            <div className="mt-2">
              <WaveAnimation />
            </div>
          )}
        </div>
      ))}
    </div>
  )
} 