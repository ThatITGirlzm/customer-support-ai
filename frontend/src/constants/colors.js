/**
 * Design token: colour palette for the Averse app.
 *
 * Brand uses Bank of Zambia-adjacent greens and neutral greys.
 * Every colour used in the app should reference this file —
 * never hard-code hex values in component or style files.
 */

const Colors = {
  // ── Brand ─────────────────────────────────────────────────────────────────
  primary:        '#1A6B3C',   // deep green  – primary actions, header bg
  primaryLight:   '#2E9159',   // lighter green – hover / pressed state
  primaryDark:    '#0F4526',   // darker green – active / selected state
  accent:         '#F5A623',   // amber        – warnings, highlights

  // ── Semantic ───────────────────────────────────────────────────────────────
  success:        '#2E9159',
  warning:        '#F5A623',
  danger:         '#D0392B',
  info:           '#2F80ED',

  // ── Action badges (mirror backend Action enum) ─────────────────────────────
  actionAnswer:   '#2E9159',   // ANSWER_FROM_SOURCE
  actionAbstain:  '#F5A623',   // ABSTAIN_NOT_IN_SOURCES
  actionRefer:    '#2F80ED',   // REFER_HUMAN
  actionBlock:    '#D0392B',   // BLOCK_INJECTION
  actionInvalid:  '#888888',   // INVALID_REQUEST
  actionUnavail:  '#888888',   // SERVICE_UNAVAILABLE
  actionDecline:  '#F5A623',   // DECLINE_OUT_OF_SCOPE

  // ── Neutrals ───────────────────────────────────────────────────────────────
  white:          '#FFFFFF',
  offWhite:       '#F7F8FA',
  surfaceLight:   '#EEF1F5',
  border:         '#DDE2EA',
  textMuted:      '#8A94A6',
  textSecondary:  '#4A5568',
  textPrimary:    '#1A202C',
  black:          '#000000',

  // ── Chat bubbles ───────────────────────────────────────────────────────────
  bubbleUser:     '#1A6B3C',   // user message background
  bubbleUserText: '#FFFFFF',
  bubbleBot:      '#FFFFFF',   // bot message background
  bubbleBotText:  '#1A202C',
  bubbleBotBorder:'#DDE2EA',

  // ── Background layers ─────────────────────────────────────────────────────
  screenBg:       '#F7F8FA',
  cardBg:         '#FFFFFF',
  inputBg:        '#FFFFFF',
  headerBg:       '#1A6B3C',
};

export default Colors;
