const API_BASE = '/api';

export async function fetchModels() {
  const response = await fetch(`${API_BASE}/models`);
  if (!response.ok) throw new Error('Failed to fetch models');
  const data = await response.json();
  return data.models;
}

export async function fetchModelPrices(modelId, days = 90) {
  const response = await fetch(`${API_BASE}/models/${modelId}/prices?days=${days}`);
  if (!response.ok) throw new Error('Failed to fetch price history');
  return response.json();
}

export async function fetchModelListings(modelId, options = {}) {
  const { limit = 50, offset = 0, sortBy = 'price', sortOrder = 'asc' } = options;
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
    sort_by: sortBy,
    sort_order: sortOrder
  });
  const response = await fetch(`${API_BASE}/models/${modelId}/listings?${params}`);
  if (!response.ok) throw new Error('Failed to fetch listings');
  return response.json();
}

export async function fetchStats() {
  const response = await fetch(`${API_BASE}/stats`);
  if (!response.ok) throw new Error('Failed to fetch stats');
  return response.json();
}

export async function fetchSettings() {
  const response = await fetch(`${API_BASE}/settings`);
  if (!response.ok) throw new Error('Failed to fetch settings');
  return response.json();
}

export async function updateSettings(settings) {
  const response = await fetch(`${API_BASE}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  });
  if (!response.ok) throw new Error('Failed to update settings');
  return response.json();
}

export async function triggerScrape(modelId = null) {
  const url = modelId ? `${API_BASE}/scrape?model_id=${modelId}` : `${API_BASE}/scrape`;
  const response = await fetch(url, { method: 'POST' });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to trigger scrape');
  }
  return response.json();
}

export async function fetchScrapeStatus() {
  const response = await fetch(`${API_BASE}/scrape/status`);
  if (!response.ok) throw new Error('Failed to fetch scrape status');
  return response.json();
}
