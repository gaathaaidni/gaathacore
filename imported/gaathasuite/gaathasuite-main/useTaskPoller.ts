import { useState, useEffect } from 'react';

interface TaskStatus {
  task_id: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILURE' | 'RETRY' | 'STARTED';
  result: any;
}

/**
 * A custom React hook to poll for the status of a Celery background task.
 *
 * @param taskId The ID of the task to poll. Polling starts when this is not null.
 * @param interval The polling interval in milliseconds. Defaults to 2000ms.
 * @returns The latest status and result of the task.
 */
export const useTaskPoller = (taskId: string | null, interval: number = 2000) => {
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(false);

  useEffect(() => {
    if (!taskId) {
      // If no taskId, reset state and stop polling.
      setTaskStatus(null);
      setIsPolling(false);
      return;
    }

    setIsPolling(true);
    const poller = setInterval(async () => {
      try {
        const response = await fetch(`/api/v2/ai/tools/task-status/${taskId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch task status');
        }
        const data: TaskStatus = await response.json();
        setTaskStatus(data);

        // Stop polling if the task is complete (SUCCESS or FAILURE)
        if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
          clearInterval(poller);
          setIsPolling(false);
        }
      } catch (error) {
        console.error('Task polling error:', error);
        // Stop polling on error to prevent spamming a broken endpoint.
        clearInterval(poller);
        setIsPolling(false);
        setTaskStatus({
          task_id: taskId,
          status: 'FAILURE',
          result: 'Failed to poll task status.',
        });
      }
    }, interval);

    // Cleanup function to stop polling when the component unmounts or taskId changes.
    return () => {
      clearInterval(poller);
    };
  }, [taskId, interval]);

  return { taskStatus, isPolling };
};