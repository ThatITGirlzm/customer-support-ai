import { REQUESTS_ENDPOINT } from "../config";

const DISPLAYABLE_ACTIONS = new Set([
  "ABSTAIN_NOT_IN_SOURCES",
  "BLOCK_INJECTION",
  "REFER_HUMAN",
  "INVALID_REQUEST",
  "SERVICE_UNAVAILABLE",
]);

export class UnsupportedResponseError extends Error {
  constructor() {
    super("The service returned a response this app is not approved to display.");
    this.name = "UnsupportedResponseError";
  }
}

export async function sendQuestion(question, signal) {
  let response;

  try {
    response = await fetch(REQUESTS_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
      signal,
    });
  } catch {
    throw new Error("NETWORK_UNAVAILABLE");
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error("INVALID_SERVICE_RESPONSE");
  }

  if (!response.ok && response.status !== 422) {
    throw new Error("SERVICE_UNAVAILABLE");
  }

  if (
    !payload ||
    typeof payload !== "object" ||
    !DISPLAYABLE_ACTIONS.has(payload.action) ||
    typeof payload.response_text !== "string" ||
    (response.status === 422 && payload.action !== "INVALID_REQUEST")
  ) {
    throw new UnsupportedResponseError();
  }

  return {
    action: payload.action,
    responseText: payload.response_text,
    reasonCode: typeof payload.reason_code === "string" ? payload.reason_code : "",
  };
}
