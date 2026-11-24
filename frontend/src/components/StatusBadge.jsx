/**
 * StatusBadge
 *
 * A small pill that labels an Action type or a referral state.
 * Colour is driven entirely by responseCardStyles — no inline colour here.
 *
 * Props:
 *   action {string}  - One of the backend Action enum values.
 *   style  {object}  - Optional extra container style.
 */

import React from 'react';
import { View, Text } from 'react-native';

import Strings             from '../constants/strings';
import responseCardStyles  from '../styles/responseCardStyles';

// Map each Action value to the badge + text style pair from responseCardStyles.
const ACTION_STYLE_MAP = {
  ANSWER_FROM_SOURCE:     ['badgeAnswer',  'badgeAnswerText'],
  ABSTAIN_NOT_IN_SOURCES: ['badgeAbstain', 'badgeAbstainText'],
  REFER_HUMAN:            ['badgeRefer',   'badgeReferText'],
  DECLINE_OUT_OF_SCOPE:   ['badgeAbstain', 'badgeAbstainText'],
  BLOCK_INJECTION:        ['badgeBlock',   'badgeBlockText'],
  INVALID_REQUEST:        ['badgeInvalid', 'badgeInvalidText'],
  SERVICE_UNAVAILABLE:    ['badgeUnavail', 'badgeUnavailText'],
};

export default function StatusBadge({ action, style }) {
  const [bgKey, textKey] = ACTION_STYLE_MAP[action] ?? ['badgeInvalid', 'badgeInvalidText'];
  const label = Strings.actions[action] ?? action;

  return (
    <View style={[responseCardStyles.badge, responseCardStyles[bgKey], style]}>
      <Text style={[responseCardStyles.badgeText, responseCardStyles[textKey]]}>
        {label}
      </Text>
    </View>
  );
}
