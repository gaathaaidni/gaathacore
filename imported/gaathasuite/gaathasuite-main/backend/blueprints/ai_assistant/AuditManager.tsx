import React, { useState } from 'react';
import { useTaskPoller } from '../hooks/useTaskPoller';

export const AuditManager: React.FC = () => {
  const [taskId, setTaskId] = useState<string | null>(null);
  const { taskStatus, isPolling } = useTaskPoller(taskId);

  const handleTriggerAudit = async () => {
    try {
      // Reset previous status
      setTaskId(null);

      const response = await fetch('/api/v2/ai/tools/trigger-long-audit', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to trigger audit.');
      }

      const data = await response.json();
      setTaskId(data.task_id);
    } catch (error) {
      console.error(error);
      // Handle UI error state here
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', maxWidth: '500px' }}>
      <h2>Audit Management</h2>
      <p>
        Trigger a long-running background audit task. The status will be polled automatically.
        Upon completion, a WebSocket notification will be sent.
      </p>
      <button onClick={handleTriggerAudit} disabled={isPolling}>
        {isPolling ? 'Audit in Progress...' : 'Trigger New Audit'}
      </button>

      {taskStatus && (
        <div style={{ marginTop: '20px', padding: '10px', background: '#f0f0f0' }}>
          <h3>Task Status</h3>
          <p>
            <strong>Task ID:</strong> {taskStatus.task_id}
          </p>
          <p>
            <strong>Status:</strong> {taskStatus.status}
          </p>
          {taskStatus.status === 'SUCCESS' && (
            <p>
              <strong>Result:</strong> {JSON.stringify(taskStatus.result)}
            </p>
          )}
        </div>
      )}
    </div>
  );
};