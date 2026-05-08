import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

// The chat microservice runs on port 8001.
// We derive the host from the main API URL so it works on localhost AND network (phone).
const mainBase = import.meta.env.VITE_API_BASE_URL as string || 'http://localhost:8000/api/';
// Replace the port with 8001 and strip the trailing path
const chatBase = mainBase.replace(/:\d+(\/.*)?$/, ':8001/');

const chatApi = axios.create({
  baseURL: chatBase,
  timeout: 10000,
  headers: {
    Accept: 'application/json',
  },
});

chatApi.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    const token = authStore.authToken;
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default chatApi;
