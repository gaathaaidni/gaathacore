export const authFetch = async (url, options = {}) => {
  let token = localStorage.getItem('token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(url, { ...options, headers });

  // If unauthorized, attempt to refresh the token using the secure cookie
  if (response.status === 401) {
    const refreshRes = await fetch('/auth/refresh', { method: 'POST' });
    
    if (refreshRes.ok) {
      const data = await refreshRes.json();
      localStorage.setItem('token', data.access_token);
      
      // Retry the original request with the new token
      headers['Authorization'] = `Bearer ${data.access_token}`;
      response = await fetch(url, { ...options, headers });
    } else {
      // Refresh failed, clear session
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
  }

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'API Request failed');
  }
  return response.json();
};