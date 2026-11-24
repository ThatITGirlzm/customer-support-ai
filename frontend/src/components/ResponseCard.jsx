/**
 * ResponseCard
 *
 * Renders a structured backend ProcessResponse inside a card bubble.
 * Layout (from top to bottom):
 *   1. Coloured accent bar reflecting the action type.
 *   2. Action badge + intent label row.
 *   3. Response text.
 *   4. Citations list (when present).
 *   5. Referral state chip (when present).
 *   6. Collapsible metadata row (request ID, reason code).
 *
 * Props:
 *   response {ProcessResponse} - Full response object from postQuestion().
 */

import React, { useState, useCallback } from 'react';
import { View, Text, Pressable } from 'react-native';

import Colors             from '../constants/colors';
import Strings            from '../constants/strings';
import responseCardStyles from '../styles/responseCardStyles';
import StatusBadge        from './StatusBadge';
import CitationItem       from './CitationItem';

// Map action → accent bar colour
const ACTION_COLOR = {
  ANSWER_FROM_SOURCE:     Colors.actionAnswer,
  ABSTAIN_NOT_IN_SOURCES: Colors.actionAbstain,
  REFER_HUMAN:            Colors.actionRefer,
  DECLINE_OUT_OF_SCOPE:   Colors.actionDecline,
  BLOCK_INJECTION:        Colors.actionBlock,
  INVALID_REQUEST:        Colors.actionInvalid,
  SERVICE_UNAVAILABLE:    Colors.actionUnavail,
};

export default function ResponseCard({ response }) {
  const [metaExpanded, setMetaExpanded] = useState(false);
  const toggleMeta = useCallback(() => setMetaExpanded(v => !v), []);

  const {
    request_id,
    action,
    response_text,
    intent,
    citations = [],
    reason_code,
    referral_state,
    demonstration,
  } = response;

  const accentColor = ACTION_COLOR[action] ?? Colors.textMuted;
  const hasCitations = citations.length > 0;
  const hasReferral  = referral_state != null;
  const hasDemoId    = demonstration?.complaint_id != null;

  return (
    <View style={responseCardStyles.card}>
      {/* ── Accent bar ───────────────────────────────────────────────────── */}
      <View style={[responseCardStyles.cardAccentBar, { backgroundColor: accentColor }]} />

      <View style={responseCardStyles.cardBody}>

        {/* ── Action badge + intent ──────────────────────────────────────── */}
        <View style={responseCardStyles.cardHeaderRow}>
          <StatusBadge action={action} />
          {intent ? (
            <Text style={responseCardStyles.metaValue}>
              {intent.replace(/_/g, ' ')}
            </Text>
          ) : null}
        </View>

        {/* ── Response text ─────────────────────────────────────────────── */}
        <Text style={responseCardStyles.responseText}>{response_text}</Text>

        {/* ── Citations ─────────────────────────────────────────────────── */}
        {hasCitations && (
          <>
            <View style={responseCardStyles.cardDivider} />
            <Text style={responseCardStyles.citationsHeading}>
              {Strings.responseCitations}
            </Text>
            {citations.map(c => (
              <CitationItem key={c.passage_id} citation={c} />
            ))}
          </>
        )}

        {/* ── Referral state ────────────────────────────────────────────── */}
        {hasReferral && (
          <>
            <View style={responseCardStyles.cardDivider} />
            <View style={responseCardStyles.metaItem}>
              <Text style={responseCardStyles.metaLabel}>
                {Strings.responseReferral}
              </Text>
              <Text style={responseCardStyles.metaValue}>
                {'  '}{Strings.referralStates[referral_state] ?? referral_state}
              </Text>
            </View>
          </>
        )}

        {/* ── Demo complaint ID ─────────────────────────────────────────── */}
        {hasDemoId && (
          <View style={responseCardStyles.metaItem}>
            <Text style={responseCardStyles.metaLabel}>Demo ID</Text>
            <Text style={responseCardStyles.metaValue}>
              {'  '}{demonstration.complaint_id}
            </Text>
          </View>
        )}

        {/* ── Collapsible metadata ─────────────────────────────────────── */}
        <Pressable onPress={toggleMeta} accessibilityRole="button"
          accessibilityLabel={metaExpanded ? 'Hide request details' : 'Show request details'}>
          <Text style={[responseCardStyles.metaValue, { textDecorationLine: 'underline' }]}>
            {metaExpanded ? '▲ Hide details' : '▼ Details'}
          </Text>
        </Pressable>

        {metaExpanded && (
          <View style={responseCardStyles.metaRow}>
            <View style={responseCardStyles.metaItem}>
              <Text style={responseCardStyles.metaLabel}>
                {Strings.responseRequestId}
              </Text>
              <Text style={responseCardStyles.metaValue} selectable>
                {'  '}{request_id}
              </Text>
            </View>
            {reason_code && (
              <View style={responseCardStyles.metaItem}>
                <Text style={responseCardStyles.metaLabel}>
                  {Strings.responseReasonCode}
                </Text>
                <Text style={responseCardStyles.metaValue}>
                  {'  '}{reason_code}
                </Text>
              </View>
            )}
          </View>
        )}

      </View>
    </View>
  );
}
