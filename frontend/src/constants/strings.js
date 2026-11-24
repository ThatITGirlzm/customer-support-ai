/**
 * UI copy for the Averse app.
 *
 * Centralising strings here makes it easy to audit wording,
 * apply translations later, or swap copy without touching
 * component files.
 */

const Strings = {
  // ── App identity ────────────────────────────────────────────────────────────
  appName:        'Averse',
  appTagline:     'Consumer Finance Assistant',
  appDescription:
    'Get clear, source-backed answers about your rights as a financial consumer in Zambia. ' +
    'Powered by approved Bank of Zambia publications.',

  // ── Navigation labels ────────────────────────────────────────────────────────
  navHome:  'Home',
  navChat:  'Ask a Question',
  navAbout: 'About',

  // ── Home screen ──────────────────────────────────────────────────────────────
  homeHeading:    'How can I help you today?',
  homeSubheading: 'Ask anything about financial consumer rights, complaint procedures, or licensed institutions in Zambia.',
  homeStartBtn:   'Start a Conversation',
  homePromptHint: 'Try: "How do I file a complaint with the Bank of Zambia?"',

  homeSuggestionsHeading: 'Suggested questions',
  homeSuggestions: [
    'How do I file a complaint with the Bank of Zambia?',
    'What are my rights as a bank customer?',
    'How do I check if a financial institution is licensed?',
    'What is the BoZ consumer protection mandate?',
  ],

  // ── Chat screen ──────────────────────────────────────────────────────────────
  chatPlaceholder:  'Type your question here…',
  chatSendBtn:      'Send',
  chatEmptyHint:    'Your conversation will appear here.',
  chatThinking:     'Averse is thinking…',
  chatNewConversation: 'New Conversation',
  chatClearConfirmTitle: 'Clear conversation?',
  chatClearConfirmMsg:   'This will remove all messages from the current session.',
  chatClearConfirmOk:    'Clear',
  chatClearConfirmCancel: 'Cancel',

  // ── Response card ────────────────────────────────────────────────────────────
  responseRequestId:  'Request ID',
  responseCitations:  'Sources',
  responseReferral:   'Referral status',
  responseReasonCode: 'Reason',

  // ── Action labels (mirror backend Action enum) ────────────────────────────────
  actions: {
    ANSWER_FROM_SOURCE:   'Answered',
    ABSTAIN_NOT_IN_SOURCES: 'No answer available',
    REFER_HUMAN:          'Referred to human support',
    DECLINE_OUT_OF_SCOPE: 'Out of scope',
    BLOCK_INJECTION:      'Request blocked',
    INVALID_REQUEST:      'Invalid request',
    SERVICE_UNAVAILABLE:  'Service unavailable',
  },

  // ── Referral state labels ────────────────────────────────────────────────────
  referralStates: {
    NOT_SENT:               'Not sent',
    SUBMITTED:              'Submitted',
    DELIVERY_UNCONFIRMED:   'Delivery unconfirmed',
  },

  // ── Error / status messages ──────────────────────────────────────────────────
  errorNetworkTitle:   'Connection error',
  errorNetworkMsg:     'Could not reach the Averse service. Check that the backend is running and try again.',
  errorGenericTitle:   'Something went wrong',
  errorGenericMsg:     'An unexpected error occurred. Please try again.',
  errorEmptyQuestion:  'Please type a question before sending.',
  errorQuestionTooLong:'Your question is too long. Please shorten it to 2 000 characters or fewer.',

  // ── About screen ─────────────────────────────────────────────────────────────
  aboutHeading:        'About Averse',
  aboutVersion:        'Prototype v0.1.0',
  aboutBody:
    'Averse is a local prototype that helps financial consumers in Zambia find information ' +
    'about their rights, complaint procedures, and licensed financial institutions.\n\n' +
    'All answers are drawn exclusively from approved Bank of Zambia publications. ' +
    'Averse does not provide legal advice and is not an official complaint channel.',
  aboutDataHeading:    'Data sources',
  aboutDataBody:
    'Passages are sourced from the Zambanker newsletter and the Bank of Zambia website ' +
    '(boz.zm). Each answer includes a citation so you can read the original document.',
  aboutDisclaimerHeading: 'Disclaimer',
  aboutDisclaimerBody:
    'This is a demonstration system. No data is transmitted to a bank, the Bank of Zambia, ' +
    'or any external service. Do not use this app as your sole source of financial or legal advice.',
  aboutBackendHeading: 'Backend status',
  aboutCheckHealth:    'Check connection',
  aboutHealthOk:       '✓ Backend is reachable',
  aboutHealthFail:     '✗ Backend is not reachable',
};

export default Strings;
