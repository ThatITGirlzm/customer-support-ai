/**
 * Styles for the ResponseCard, MessageBubble, CitationItem, and StatusBadge
 * components.
 *
 * Keeping all message-display styles in one file makes it easy to retheme
 * the chat output without touching any component logic.
 */

import { StyleSheet } from 'react-native';
import Colors              from '../constants/colors';
import { Spacing, Radius, Shadow } from '../constants/spacing';
import { FontSize, FontWeight } from '../constants/typography';

const responseCardStyles = StyleSheet.create({

  // ════════════════════════════════════════════════════════════════════════════
  // MessageBubble — wraps both user and bot turns
  // ════════════════════════════════════════════════════════════════════════════

  bubbleRow: {
    flexDirection: 'row',
    marginBottom:  Spacing.sm,
  },
  bubbleRowUser: {
    justifyContent: 'flex-end',
  },
  bubbleRowBot: {
    justifyContent: 'flex-start',
  },

  // User bubble
  bubbleUser: {
    backgroundColor: Colors.bubbleUser,
    borderRadius:    Radius.lg,
    borderBottomRightRadius: Radius.xs,
    paddingHorizontal: Spacing.md,
    paddingVertical:   Spacing.sm,
    maxWidth:          '80%',
  },
  bubbleUserText: {
    fontSize:   FontSize.base,
    color:      Colors.bubbleUserText,
    lineHeight: FontSize.base * 1.5,
  },

  // Bot bubble shell (contains the ResponseCard)
  bubbleBot: {
    maxWidth:   '90%',
    marginLeft: Spacing.xs,
  },

  // Timestamp beneath a bubble
  bubbleTimestamp: {
    fontSize:  FontSize.xs,
    color:     Colors.textMuted,
    marginTop: Spacing.xxs,
    paddingHorizontal: Spacing.xs,
  },
  bubbleTimestampUser: {
    textAlign: 'right',
  },
  bubbleTimestampBot: {
    textAlign: 'left',
  },

  // ════════════════════════════════════════════════════════════════════════════
  // ResponseCard — the structured bot response container
  // ════════════════════════════════════════════════════════════════════════════

  card: {
    backgroundColor: Colors.bubbleBot,
    borderRadius:    Radius.lg,
    borderBottomLeftRadius: Radius.xs,
    borderWidth:     1,
    borderColor:     Colors.bubbleBotBorder,
    overflow:        'hidden',
    ...Shadow.sm,
  },

  // Coloured top bar that reflects the action type
  cardAccentBar: {
    height: 4,
  },

  cardBody: {
    paddingHorizontal: Spacing.md,
    paddingTop:        Spacing.sm,
    paddingBottom:     Spacing.md,
    gap:               Spacing.sm,
  },

  // Action + intent header row
  cardHeaderRow: {
    flexDirection: 'row',
    alignItems:    'center',
    gap:           Spacing.sm,
    flexWrap:      'wrap',
  },

  // Response text
  responseText: {
    fontSize:   FontSize.base,
    color:      Colors.bubbleBotText,
    lineHeight: FontSize.base * 1.6,
  },

  // Metadata row (request ID, reason code)
  metaRow: {
    flexDirection: 'row',
    flexWrap:      'wrap',
    gap:           Spacing.sm,
    marginTop:     Spacing.xs,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems:    'center',
    gap:           Spacing.xxs,
  },
  metaLabel: {
    fontSize:   FontSize.xs,
    color:      Colors.textMuted,
    fontWeight: FontWeight.semiBold,
  },
  metaValue: {
    fontSize:   FontSize.xs,
    color:      Colors.textMuted,
    fontFamily: 'monospace',
  },

  // Section divider inside the card
  cardDivider: {
    height:          1,
    backgroundColor: Colors.border,
    marginVertical:  Spacing.xs,
  },

  // Citations section heading
  citationsHeading: {
    fontSize:   FontSize.sm,
    fontWeight: FontWeight.semiBold,
    color:      Colors.textSecondary,
    marginBottom: Spacing.xs,
  },

  // ════════════════════════════════════════════════════════════════════════════
  // CitationItem — one source reference row
  // ════════════════════════════════════════════════════════════════════════════

  citationItem: {
    flexDirection:   'row',
    alignItems:      'flex-start',
    gap:             Spacing.sm,
    paddingVertical: Spacing.xs,
  },
  citationBullet: {
    width:        6,
    height:       6,
    borderRadius: 3,
    backgroundColor: Colors.primary,
    marginTop:    6,
    flexShrink:   0,
  },
  citationBody: {
    flex: 1,
    gap:  Spacing.xxs,
  },
  citationTitle: {
    fontSize:   FontSize.sm,
    fontWeight: FontWeight.semiBold,
    color:      Colors.primary,
    textDecorationLine: 'underline',
  },
  citationMeta: {
    fontSize: FontSize.xs,
    color:    Colors.textMuted,
  },
  citationSection: {
    fontSize:  FontSize.xs,
    color:     Colors.textSecondary,
    fontStyle: 'italic',
  },

  // ════════════════════════════════════════════════════════════════════════════
  // StatusBadge — pill label for action type or referral state
  // ════════════════════════════════════════════════════════════════════════════

  badge: {
    borderRadius:    Radius.pill,
    paddingVertical:   Spacing.xxs + 1,
    paddingHorizontal: Spacing.sm,
    alignSelf:       'flex-start',
  },
  badgeText: {
    fontSize:   FontSize.xs,
    fontWeight: FontWeight.semiBold,
    letterSpacing: 0.3,
  },

  // Colour variants (background + text combos)
  badgeAnswer: {
    backgroundColor: Colors.actionAnswer + '22',   // 13% opacity fill
  },
  badgeAnswerText: {
    color: Colors.actionAnswer,
  },
  badgeAbstain: {
    backgroundColor: Colors.actionAbstain + '22',
  },
  badgeAbstainText: {
    color: Colors.actionAbstain,
  },
  badgeRefer: {
    backgroundColor: Colors.actionRefer + '22',
  },
  badgeReferText: {
    color: Colors.actionRefer,
  },
  badgeBlock: {
    backgroundColor: Colors.actionBlock + '22',
  },
  badgeBlockText: {
    color: Colors.actionBlock,
  },
  badgeInvalid: {
    backgroundColor: Colors.actionInvalid + '22',
  },
  badgeInvalidText: {
    color: Colors.actionInvalid,
  },
  badgeUnavail: {
    backgroundColor: Colors.actionUnavail + '22',
  },
  badgeUnavailText: {
    color: Colors.actionUnavail,
  },
});

export default responseCardStyles;
