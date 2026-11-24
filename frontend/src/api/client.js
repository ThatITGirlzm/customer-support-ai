/**
 * HTTP client for the Averse backend.
 *
 * All network calls go through `request()`. It handles:
 *   - Base URL resolution (change BASE_URL for your machine's IP when using Expo Go)
 *   - JSON serialisation / deserialisation
 *   - Timeout via AbortController
 *   - Uniform error shape so callers never have to inspect raw fetch errors
 *
 * Never import fetch directly in screens or components — always use this module.
 */

/**
 * The backend base URL.
 *
 * When running Expo Go on a physical device, replace 'localhost' with your
 * machine's local IP address (e.g. 'http://192.168.1.42:8000').
 * The Android emulator can reach the host machine at 'http://10.0.2.2:8000'.
 *
 * This value can be overridden at runtime via the settings screen (future).
 */
export const BASE_URL = 'http://10.69.147.194:8000';


/** Default request timeout in milliseconds. */
const TIMEOUT_MS = 15_000;

/**
 * A normalised error thrown by `request()`.
 *
 * @property {number|null}  status    - HTTP status code, or null for network errors.
 * @property {string}       code      - Machine-readable error code.
 * @property {string}       message   - Human-readable explanation.
 * @property {any}          [detail]  - Raw response body when available.
 */
export class ApiError extends Error {
  constructor(message, { status = null, code = 'UNKNOWN_ERROR', detail = undefined } = {}) {
    super(message);
    this.name    = 'ApiError';
    this.status  = status;
    this.code    = code;
    this.detail  = detail;
  }
}

/**
 * Core request helper.
 *
 * @param {string} path        - Path relative to BASE_URL, e.g. '/api/v1/requests'
 * @param {object} [options]
 * @param {'GET'|'POST'} [options.method='GET']
 * @param {object} [options.body]               - JSON-serialisable request body.
 * @param {number} [options.timeoutMs]          - Override default timeout.
 * @returns {Promise<any>}                      - Parsed JSON response body.
 * @throws {ApiError}
 */
export async function request(path, { method = 'GET', body, timeoutMs = TIMEOUT_MS } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const url = `${BASE_URL}${path}`;
  const headers = { 'Content-Type': 'application/json' };

  let response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body:   body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timer);
    if (err.name === 'AbortError') {
      throw new ApiError('Request timed out. Check your connection and try again.', {
        code: 'TIMEOUT',
      });
    }
    throw new ApiError('Could not reach the Averse service. Is the backend running?', {
      code: 'NETWORK_ERROR',
    });
  } finally {
    clearTimeout(timer);
  }

  // Parse body regardless of status so we can include it in error detail.
  let data;
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  } else {
    data = await response.text().catch(() => null);
  }

  if (!response.ok) {
    throw new ApiError(
      data?.detail ?? `Server returned ${response.status}`,
      {
        status: response.status,
        code:   `HTTP_${response.status}`,
        detail: data,
      },
    );
  }

  return data;
}
