const configuredBaseUrl = process.env.EXPO_PUBLIC_AVERSE_API_BASE_URL;

export const API_BASE_URL = (configuredBaseUrl || "http://127.0.0.1:8000").replace(
  /\/+$/,
  "",
);

export const REQUESTS_ENDPOINT = `${API_BASE_URL}/api/v1/requests`;
