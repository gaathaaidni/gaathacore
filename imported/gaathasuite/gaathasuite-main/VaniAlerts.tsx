import React, { useEffect } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import { useAiAlerts } from '../hooks/useAiAlerts';

// In a real app, you would use a router hook like this.
// import { useNavigate } from 'react-router-dom';

// Assume a hook that provides the current user's organization ID
// import { useCurrentUser } from '../hooks/useCurrentUser';

/**
 * A component that renders real-time AI alerts from Vani as toast notifications.
 * It should be placed in your main App layout.
 */
export const VaniAlerts: React.FC = () => {
  // In a real app, you would get the orgId from your user session/context
  // const { currentOrgId } = useCurrentUser();
  const currentOrgId = 'your-org-id'; // Placeholder

  // Placeholder for router navigation
  // const navigate = useNavigate();

  const { alerts } = useAiAlerts(currentOrgId);

  useEffect(() => {
    if (alerts.length > 0) {
      // Get the most recent alert (it's prepended to the array)
      const latestAlert = alerts[0];

      // Use toast.custom for a fully styled component, or toast() for simpler messages.
      // Here we use toast() and leverage the icon from the payload.
      toast(
        (t) => (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            {/* Render the icon from the payload */}
            <span style={{ fontSize: '1.5rem', alignSelf: 'flex-start', marginTop: '4px' }}>{latestAlert.icon}</span>
            <div style={{ flex: 1 }}>
              {/* Render the type as a bold header */}
              <b>Vani {latestAlert.type}</b>
              <p style={{ margin: 0 }}>{latestAlert.message}</p>

              {/* If the alert has a clickable action, render it */}
              {latestAlert.action && (
                <a
                  href={latestAlert.action.url}
                  onClick={(e) => {
                    e.preventDefault();
                    // In a real SPA, you would use your router's navigation function
                    // navigate(latestAlert.action.url);
                    console.log(`Navigating to: ${latestAlert.action.url}`);
                    toast.dismiss(t.id);
                  }}
                  style={{ color: '#0052cc', fontWeight: 'bold', marginTop: '8px', display: 'inline-block' }}
                >
                  {latestAlert.action.label}
                </a>
              )}
            </div>
            <button
              style={{ border: 'none', background: 'transparent', cursor: 'pointer', alignSelf: 'flex-start' }}
              onClick={() => toast.dismiss(t.id)}
            >
              Dismiss
            </button>
          </div>
        ),
        { id: latestAlert.id, duration: 10000 } // Use alert ID to prevent duplicates
      );
    }
  }, [alerts]);

  // The <Toaster /> component is responsible for rendering the toasts.
  // It can be placed here or at the very root of your application.
  return <Toaster position="bottom-right" />;
};