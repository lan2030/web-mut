import axios from 'axios';

// Same-origin API client. Cookies are sent automatically; the CSRF token is
// injected into unsafe requests from the auth store.
const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
});

let csrfToken = null;
export function setCsrfToken(token) {
  csrfToken = token;
}

const UNSAFE = ['post', 'put', 'patch', 'delete'];
api.interceptors.request.use((config) => {
  if (csrfToken && UNSAFE.includes((config.method || 'get').toLowerCase())) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});

export default api;
