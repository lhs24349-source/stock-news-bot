import axios from 'axios';

// API 베이스 URL 결정:
// - Vercel 배포: VITE_API_URL 환경변수 + /api 접미사 사용 (Railway 백엔드 직접 호출)
// - 로컬 개발: /api 경로 → Vite devServer 프록시가 localhost:8000 으로 전달
const envUrl = import.meta.env.VITE_API_URL;
const baseURL = envUrl ? `${envUrl.replace(/\/+$/, '')}/api` : '/api';

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
