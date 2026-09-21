import { useState, useEffect, useRef } from 'react';

/**
 * Represents the structure of an AI alert message received from the WebSocket,
 * now reflecting the Vani branding and alert types.
 */
interface AiAlert {
  id: string; // A unique identifier for the alert
  message: string;
  timestamp: string;
  /**
   * The type of insight for UI rendering (e.g., 'Insight', 'Update', 'Security').
   */
  type?: 'Insight' | 'Update' | 'Security' | 'Generic';
  /**
   * An optional icon for display in toast notifications or banners.
   */
  icon?: '⚡' | '✅' | '🔒';
  /**
   * Optional action for the user to take, like navigating to a specific page.
   */
  action?: {
    // The text to display on the action button/link (e.g., "View Report").
    label: string;
    // The URL to navigate to when the action is clicked.
    url: string;
  };
}

/**
 * A custom React hook to connect to the Gaatha AI alerts WebSocket.
 * It manages the connection lifecycle and provides the latest alerts.
 *
 * @param orgId The ID of the organization to connect for. If null, no connection is made.
 * @returns An object containing the list of structured `AiAlert` objects and the current connection status.
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
        // The backend now sends a structured alert object reflecting the Vani branding.
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