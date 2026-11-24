/**
 * MessageBubble
 *
 * Renders one turn in the conversation — either a user question or a bot
 * response.  User messages are plain text bubbles aligned to the right.
 * Bot messages are ResponseCard components aligned to the left.
 *
 * Props:
 *   message {object}
 *     message.id        {string}  - Unique key (provided by ChatScreen).
 *     message.role      {'user'|'bot'}
 *     message.text      {string}  - For user messages.
 *     message.response  {object}  - ProcessResponse for bot messages.
 *     message.timestamp {Date}
 *   isLast {boolean} - Whether this is the most recent message (affects spacing).
 */

import React from 'react';
import { View, Text } from 'react-native';

import responseCardStyles from '../styles/responseCardStyles';
import ResponseCard       from './ResponseCard';

/** Format a Date to HH:MM */
function formatTime(date) {
  if (!(date instanceof Date) || isNaN(date)) return '';
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function MessageBubble({ message, isLast }) {
  const { role, text, response, timestamp } = message;
  const isUser = role === 'user';
  const timeLabel = formatTime(timestamp);

  return (
    <View style={[
      responseCardStyles.bubbleRow,
      isUser ? responseCardStyles.bubbleRowUser : responseCardStyles.bubbleRowBot,
      isLast  ? { marginBottom: 4 } : null,
    ]}>

      {isUser ? (
        /* ── User bubble ────────────────────────────────────────────────── */
        <View>
          <View style={responseCardStyles.bubbleUser}>
            <Text style={responseCardStyles.bubbleUserText}>{text}</Text>
          </View>
          {timeLabel ? (
            <Text style={[
              responseCardStyles.bubbleTimestamp,
              responseCardStyles.bubbleTimestampUser,
            ]}>
              {timeLabel}
            </Text>
          ) : null}
        </View>
      ) : (
        /* ── Bot bubble ─────────────────────────────────────────────────── */
        <View style={responseCardStyles.bubbleBot}>
          {response ? (
            <ResponseCard response={response} />
          ) : (
            /* Fallback plain text (shouldn't normally appear) */
            <View style={responseCardStyles.bubbleUser}>
              <Text style={responseCardStyles.bubbleUserText}>{text}</Text>
            </View>
          )}
          {timeLabel ? (
            <Text style={[
              responseCardStyles.bubbleTimestamp,
              responseCardStyles.bubbleTimestampBot,
            ]}>
              {timeLabel}
            </Text>
          ) : null}
        </View>
      )}

    </View>
  );
}
