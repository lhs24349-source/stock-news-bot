import axios from 'axios';

// API 베이스 URL (Vercel에서는 VITE_API_URL 환경변수 사용, 로컬에서는 Vite 프록시)
const baseURL = import.meta.env.VITE_API_URL || '/api';

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 응답 에러 공통 처리
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
