export async function fetchWithAuthToken(url: string, token: string, options: RequestInit = {}) {
  const headers = {
    ...(options.headers || {}),
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
  console.log('[fetchWithAuthToken] URL:', url);
  console.log('[fetchWithAuthToken] Token:', token);
  console.log('[fetchWithAuthToken] Headers:', headers);
  const response = await fetch(url, {
    ...options,
    headers,
  });
  if (!response.ok) {
    const errorText = await response.text();
    console.error('[fetchWithAuthToken] Error response:', errorText);
    throw new Error(`HTTP error! Status: ${response.status}`);
  }
  return response.json();
}
