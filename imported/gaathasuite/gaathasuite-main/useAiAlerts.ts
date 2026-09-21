import { useState, useEffect, useRef } from 'react';

/**
 * Represents the structure of an AI alert message received from the WebSocket.
 */
interface AiAlert {
  id: string; // A unique identifier for the alert
  message: string;
  timestamp: string;
}

/**
 * A custom React hook to connect to the Gaatha AI alerts WebSocket.
 * It manages the connection lifecycle and provides the latest alerts.
 *
 * @param orgId The ID of the organization to connect for. If null, no connection is made.
 * @returns An object containing the list of alerts and the current connection status.
 */
export const useAiAlerts = (orgId: string | null) => {
  const [alerts, setAlerts] = useState<AiAlert[]>([]);
  const [status, setStatus] = useState<'connecting' | 'open' | 'closed'>('closed');
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Do not connect if the orgId is not available.
    if (!orgId) {
      return;
    }

    // Determine WebSocket protocol (ws or wss)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v2/ai/ws/${orgId}`;

    setStatus('connecting');
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('AI Alert WebSocket connection established.');
      setStatus('open');
    };

    ws.current.onmessage = (event) => {
      try {
        const alertData: AiAlert = JSON.parse(event.data);
        // Assuming the backend sends a full alert object.
        // We prepend the new alert to the list to show the most recent first.
        setAlerts((prevAlerts) => [alertData, ...prevAlerts]);
      } catch (error) {
        console.error('Failed to parse AI alert message:', error);
      }
    };

    ws.current.onerror = (error) => {
      console.error('AI Alert WebSocket error:', error);
    };

    ws.current.onclose = () => {
      console.log('AI Alert WebSocket connection closed.');
      setStatus('closed');
    };

    // Cleanup function to close the WebSocket connection when the component unmounts
    // or when the orgId changes.
    return () => {
      ws.current?.close();
    };
  }, [orgId]); // Re-run the effect if the organization ID changes.

  return { alerts, status };
};