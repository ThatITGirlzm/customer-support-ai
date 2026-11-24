/**
 * Typed endpoint functions for the Averse backend.
 *
 * Each function maps 1-to-1 to a backend route.  Callers receive either a
 * resolved response object (matching the backend ProcessResponse schema) or a
 * thrown ApiError.
 *
 * Import only from this module in screens/components — never call `request()`
 * or `fetch()` directly outside the api/ folder.
 */

import { request } from './client';

// ─────────────────────────────────────────────────────────────────────────────
// Health
// ─────────────────────────────────────────────────────────────────────────────

/**
 * GET /health
 * Liveness probe.  Returns { status: 'ok', mode: 'local-prototype' } on success.
 *
 * @returns {Promise<{ status: string, mode: string }>}
 */
export async function getHealth() {
  return request('/health');
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Q&A endpoint
// ─────────────────────────────────────────────────────────────────────────────

/**
 * POST /api/v1/requests
 * Submit a question and receive a ProcessResponse.
 *
 * @param {string} question  - The user's question (max 2000 characters).
 * @returns {Promise<ProcessResponse>}
 *
 * @typedef {Object} ProcessResponse
 * @property {string}            request_id
 * @property {Action}            action
 * @property {string}            response_text
 * @property {string|null}       intent
 * @property {Citation[]}        citations
 * @property {string|null}       reason_code
 * @property {string|null}       referral_state
 * @property {string|null}       referral_reference
 * @property {DemonstrationStatus|null} demonstration
 *
 * @typedef {'ANSWER_FROM_SOURCE'|'ABSTAIN_NOT_IN_SOURCES'|'REFER_HUMAN'|
 *           'DECLINE_OUT_OF_SCOPE'|'BLOCK_INJECTION'|'INVALID_REQUEST'|
 *           'SERVICE_UNAVAILABLE'} Action
 *
 * @typedef {Object} Citation
 * @property {string}       passage_id
 * @property {string}       source_id
 * @property {string}       source_title
 * @property {string}       source_url
 * @property {string|null}  publication_date
 * @property {string}       accessed_date
 * @property {string}       section_or_page
 *
 * @typedef {Object} DemonstrationStatus
 * @property {string|null}  complaint_id
 * @property {string}       record_state
 * @property {string}       notification_state
 * @property {boolean}      notification_delivered
 * @property {boolean}      external_referral_submitted
 */
export async function postQuestion(question) {
  return request('/api/v1/requests', {
    method: 'POST',
    body:   { question },
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Demo complaint endpoint (loopback-only on the backend)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * POST /api/v1/demo/complaints
 * Submit a synthetic demo complaint.
 *
 * The backend restricts this route to loopback clients (127.0.0.1 / ::1).
 * It will return 403 from any other origin, including a physical device.
 * Only usable when the app is running in a simulator against localhost.
 *
 * @param {string} question
 * @returns {Promise<ProcessResponse>}
 */
export async function postDemoComplaint(question) {
  return request('/api/v1/demo/complaints', {
    method: 'POST',
    body:   {
      question,
      demo_declaration: 'SYNTHETIC_DEMO_ONLY',
    },
  });
}
