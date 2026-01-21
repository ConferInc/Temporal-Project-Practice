import axios from 'axios';

// Vite exposes env variables via import.meta.env
// Use the explicitly defined VITE_API_URL or fallback to localhost
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request Interceptor: Add Bearer Token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401 Unauthorized
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // If we get a 401, the token is likely expired or invalid
            // Clear storage and reload to force logout/login redirect
            // We check if we are already on the login page to avoid infinite loops
            if (!window.location.pathname.includes('/login')) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
