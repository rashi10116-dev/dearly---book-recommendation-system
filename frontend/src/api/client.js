const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export const getAuthToken = () => localStorage.getItem('dearly_token');
export const setAuthToken = (token) => {
  if (token) localStorage.setItem('dearly_token', token);
  else localStorage.removeItem('dearly_token');
};

async function apiRequest(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  if (options.body instanceof FormData) {
    delete headers['Content-Type']; // Let browser set multipart boundary
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'An error occurred';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Auth
  auth: {
    register: (email, username, password) =>
      apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, username, password }),
      }),
    login: (username_or_email, password) =>
      apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username_or_email, password }),
      }),
    getMe: () => apiRequest('/auth/me'),
    logout: () => {
      setAuthToken(null);
      return Promise.resolve({ success: true });
    },
  },

  // Preferences
  preferences: {
    get: () => apiRequest('/preferences'),
    save: (prefs) =>
      apiRequest('/preferences', {
        method: 'POST',
        body: JSON.stringify(prefs),
      }),
  },

  // Books
  books: {
    list: (params = {}) => {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          query.append(key, val);
        }
      });
      const qs = query.toString();
      return apiRequest(`/books${qs ? `?${qs}` : ''}`);
    },
    get: (id) => apiRequest(`/books/${id}`),
    genres: () => apiRequest('/books/genres'),
    tropes: () => apiRequest('/books/tropes'),
    discovery: () => apiRequest('/books/discovery'),
    discoverySection: (sectionId, params = {}) => {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          query.append(key, val);
        }
      });
      const qs = query.toString();
      return apiRequest(`/books/discovery/${sectionId}${qs ? `?${qs}` : ''}`);
    },
  },

  // Reading history
  reading: {
    list: (params = {}) => {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          query.append(key, val);
        }
      });
      const qs = query.toString();
      return apiRequest(`/reading${qs ? `?${qs}` : ''}`);
    },
    stats: () => apiRequest('/reading/stats'),
    addOrUpdate: (entryData) =>
      apiRequest('/reading', {
        method: 'POST',
        body: JSON.stringify(entryData),
      }),
    update: (entryId, updateData) =>
      apiRequest(`/reading/${entryId}`, {
        method: 'PUT',
        body: JSON.stringify(updateData),
      }),
    delete: (entryId) =>
      apiRequest(`/reading/${entryId}`, {
        method: 'DELETE',
      }),
  },

  // Recommendations
  recommendations: {
    getDashboard: () => apiRequest('/recommendations/dashboard'),
    recompute: () =>
      apiRequest('/recommendations/recompute', {
        method: 'POST',
      }),
  },

  // Dataset
  dataset: {
    importCsv: (file) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiRequest('/dataset/import-csv', {
        method: 'POST',
        body: formData,
      });
    },
    resetSeed: () =>
      apiRequest('/dataset/reset-seed', {
        method: 'POST',
      }),
    getStats: () => apiRequest('/dataset/stats'),
  },
};
