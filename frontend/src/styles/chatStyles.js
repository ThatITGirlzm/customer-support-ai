/**
 * Styles for the Chat screen and its message list.
 *
 * Covers the full-screen layout, the message list, the composer bar
 * (text input + send button), and the typing-indicator row.
 * Individual bubble and response-card styles live in their own component
 * style files (messageBubbleStyles via MessageBubble, responseCardStyles).
 */

import { StyleSheet } from 'react-native';
import Colors              from '../constants/colors';
import { Spacing, Radius, Shadow } from '../constants/spacing';
import { FontSize, FontWeight } from '../constants/typography';

const chatStyles = StyleSheet.create({

  // ── Screen shell ─────────────────────────────────────────────────────────────
  screen: {
    flex:            1,
    backgroundColor: Colors.screenBg,
  },

  // ── Message list ──────────────────────────────────────────────────────────────
  messageList: {
    flex: 1,
  },
  messageListContent: {
    paddingHorizontal: Spacing.md,
    paddingTop:        Spacing.md,
    paddingBottom:     Spacing.lg,
  },

  // ── Empty state inside the list ───────────────────────────────────────────────
  emptyWrapper: {
    flex:           1,
    alignItems:     'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.xl,
    paddingVertical:   Spacing.xxl,
  },
  emptyIcon: {
    fontSize:    48,
    marginBottom: Spacing.md,
  },
  emptyText: {
    fontSize:  FontSize.base,
    color:     Colors.textMuted,
    textAlign: 'center',
  },

  // ── Typing indicator ──────────────────────────────────────────────────────────
  typingRow: {
    flexDirection:  'row',
    alignItems:     'center',
    paddingHorizontal: Spacing.md,
    paddingVertical:   Spacing.sm,
    gap:            Spacing.sm,
  },
  typingBubble: {
    backgroundColor: Colors.bubbleBot,
    borderRadius:    Radius.lg,
    borderWidth:     1,
    borderColor:     Colors.bubbleBotBorder,
    paddingHorizontal: Spacing.md,
    paddingVertical:   Spacing.sm,
    flexDirection:   'row',
    alignItems:      'center',
    gap:             Spacing.xs,
  },
  typingDot: {
    width:        6,
    height:       6,
    borderRadius: 3,
    backgroundColor: Colors.textMuted,
  },
  typingLabel: {
    fontSize: FontSize.sm,
    color:    Colors.textMuted,
  },

  // ── Composer bar ──────────────────────────────────────────────────────────────
  composerBar: {
    flexDirection:     'row',
    alignItems:        'flex-end',
    paddingHorizontal: Spacing.md,
    paddingVertical:   Spacing.sm,
    backgroundColor:   Colors.cardBg,
    borderTopWidth:    1,
    borderTopColor:    Colors.border,
    gap:               Spacing.sm,
    ...Shadow.sm,
  },
  inputWrapper: {
    flex:            1,
    backgroundColor: Colors.inputBg,
    borderRadius:    Radius.xl,
    borderWidth:     1.5,
    borderColor:     Colors.border,
    paddingHorizontal: Spacing.md,
    paddingVertical:   Spacing.sm,
    minHeight:       44,
    maxHeight:       120,
    justifyContent:  'center',
  },
  inputWrapperFocused: {
    borderColor: Colors.primary,
  },
  input: {
    fontSize:  FontSize.base,
    color:     Colors.textPrimary,
    padding:   0,           // remove default Android padding
    margin:    0,
    textAlignVertical: 'top',
  },
  sendBtn: {
    width:           44,
    height:          44,
    borderRadius:    22,
    backgroundColor: Colors.primary,
    alignItems:      'center',
    justifyContent:  'center',
    ...Shadow.sm,
  },
  sendBtnDisabled: {
    backgroundColor: Colors.surfaceLight,
  },
  sendBtnText: {
    fontSize:   FontSize.lg,
    color:      Colors.white,
    lineHeight: 44,
    textAlign:  'center',
  },
  sendBtnTextDisabled: {
    color: Colors.textMuted,
  },
  charCount: {
    fontSize:  FontSize.xs,
    color:     Colors.textMuted,
    textAlign: 'right',
    paddingRight: Spacing.xs,
    paddingBottom: Spacing.xxs,
  },
  charCountWarn: {
    color: Colors.warning,
  },

  // ── Scroll-to-bottom FAB ─────────────────────────────────────────────────────
  scrollFab: {
    position:        'absolute',
    right:           Spacing.md,
    bottom:          Spacing.lg,
    width:           36,
    height:          36,
    borderRadius:    18,
    backgroundColor: Colors.primary,
    alignItems:      'center',
    justifyContent:  'center',
    ...Shadow.md,
  },
  scrollFabText: {
    color:    Colors.white,
    fontSize: FontSize.sm,
    fontWeight: FontWeight.bold,
  },
});

export default chatStyles;
