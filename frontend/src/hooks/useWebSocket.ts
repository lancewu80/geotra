import { useEffect, useRef, useState } from 'react'
import { WS_URL } from '../api/client'
import type { LiveEvent } from '../types'

export function useLiveEvents(onEvent: (event: LiveEvent) => void) {
  const [connected, setConnected] = useState(false)
  const handlerRef = useRef(onEvent)
  handlerRef.current = onEvent

  useEffect(() => {
    let socket: WebSocket
    let retryTimer: ReturnType<typeof setTimeout>
    let cancelled = false

    function connect() {
      socket = new WebSocket(WS_URL)
      socket.onopen = () => setConnected(true)
      socket.onclose = () => {
        setConnected(false)
        if (!cancelled) retryTimer = setTimeout(connect, 2000)
      }
      socket.onerror = () => socket.close()
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as LiveEvent
          handlerRef.current(data)
        } catch {
          // ignore malformed frames
        }
      }
    }

    connect()
    return () => {
      cancelled = true
      clearTimeout(retryTimer)
      socket?.close()
    }
  }, [])

  return { connected }
}
