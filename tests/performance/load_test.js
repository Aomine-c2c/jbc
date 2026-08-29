import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 }, // Ramp up to 20 users
    { duration: '1m', target: 20 },  // Stay at 20 users
    { duration: '30s', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
  },
};

const BASE_URL = 'http://localhost:8000/api/v1';

export default function () {
  // We simulate a basic health check and a mock login for load testing
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });

  // Simulated Login (Load Test credentials should exist in DB)
  /*
  const loginRes = http.post(`${BASE_URL}/iam/auth/login`, {
    username: 'loadtest@example.com',
    password: 'Password123!'
  });
  check(loginRes, {
    'login status is 200': (r) => r.status === 200,
  });
  */

  sleep(1);
}
