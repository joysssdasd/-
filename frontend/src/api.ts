import axios from 'axios';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: apiBaseUrl
});

type RequestOptions = {
  token?: string | null;
};

api.interceptors.request.use((config) => {
  const storedToken = localStorage.getItem('access_token');
  if (storedToken && config.headers) {
    config.headers.Authorization = `Bearer ${storedToken}`;
  }
  return config;
});

export default api;
export type { RequestOptions };
