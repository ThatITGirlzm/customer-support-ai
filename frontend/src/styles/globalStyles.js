/**
 * Global / shared styles.
 *
 * These rules apply across the whole app — screen wrappers, generic cards,
 * dividers, utility classes. Import specific-purpose style files (chatStyles,
 * headerStyles, etc.) for component-level overrides.
 */

import { StyleSheet } from 'react-native';
import Colors          from '../constants/colors';
import { Spacing, Radius, Shadow } from '../constants/spacing';
import { FontSize, FontWeight, TextStyles } from '../constants/typography';

const globalStyles = StyleSheet.create({

  // ── Screen wrappers ─────────────────────────────────────────────────────────
  screen: {
    flex:            1,
    backgroundColor: Colors.screenBg,
  },
  screenPadded: {
    flex:            1,
    backgroundColor: Colors.screenBg,
    paddingHorizontal: Spacing.md,
  },
  scrollContent: {
    paddingHorizontal: Spacing.md,
    paddingBottom:     Spacing.xxl,
  },

  // ── Generic card ────────────────────────────────────────────────────────────
  card: {
    backgroundColor:  Colors.cardBg,
    borderRadius:     Radius.md,
    padding:          Spacing.md,
    marginBottom:     Spacing.md,
    ...Shadow.sm,
  },
  cardFlat: {
    backgroundColor: Colors.cardBg,
    borderRadius:    Radius.md,
    padding:         Spacing.md,
    marginBottom:    Spacing.md,
    borderWidth:     1,
    borderColor:     Colors.border,
  },

  // ── Row / layout helpers ────────────────────────────────────────────────────
  row: {
    flexDirection: 'row',
    alignItems:    'center',
  },
  rowSpaceBetween: {
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'space-between',
  },
  centered: {
    alignItems:     'center',
    justifyContent: 'center',
  },

  // ── Divider ─────────────────────────────────────────────────────────────────
  divider: {
    height:          1,
    backgroundColor: Colors.border,
    marginVertical:  Spacing.md,
  },

  // ── Typography ───────────────────────────────────────────────────────────────
  h1: {
    ...TextStyles.h1,
    color:        Colors.textPrimary,
    marginBottom: Spacing.sm,
  },
  h2: {
    ...TextStyles.h2,
    color:        Colors.textPrimary,
    marginBottom: Spacing.sm,
  },
  h3: {
    ...TextStyles.h3,
    color:        Colors.textPrimary,
    marginBottom: Spacing.xs,
  },
  bodyLarge: {
    ...TextStyles.bodyLarge,
    color: Colors.textPrimary,
  },
  body: {
    ...TextStyles.body,
    color: Colors.textPrimary,
  },
  bodySmall: {
    ...TextStyles.bodySmall,
    color: Colors.textSecondary,
  },
  caption: {
    ...TextStyles.caption,
    color: Colors.textMuted,
  },
  label: {
    ...TextStyles.label,
    color: Colors.textSecondary,
  },
  muted: {
    ...TextStyles.body,
    color: Colors.textMuted,
  },
  mono: {
    ...TextStyles.mono,
    color: Colors.textMuted,
  },

  // ── Buttons ──────────────────────────────────────────────────────────────────
  btnPrimary: {
    backgroundColor: Colors.primary,
    borderRadius:    Radius.pill,
    paddingVertical:   Spacing.sm + 2,
    paddingHorizontal: Spacing.lg,
    alignItems:      'center',
    justifyContent:  'center',
    ...Shadow.sm,
  },
  btnPrimaryText: {
    ...TextStyles.label,
    color:      Colors.white,
    fontSize:   FontSize.base,
    fontWeight: FontWeight.semiBold,
  },
  btnOutline: {
    borderWidth:     1.5,
    borderColor:     Colors.primary,
    borderRadius:    Radius.pill,
    paddingVertical:   Spacing.sm + 2,
    paddingHorizontal: Spacing.lg,
    alignItems:      'center',
    justifyContent:  'center',
  },
  btnOutlineText: {
    ...TextStyles.label,
    color:      Colors.primary,
    fontSize:   FontSize.base,
    fontWeight: FontWeight.semiBold,
  },
  btnDisabled: {
    opacity: 0.45,
  },

  // ── Empty state ───────────────────────────────────────────────────────────────
  emptyState: {
    flex:           1,
    alignItems:     'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.xl,
    paddingVertical:   Spacing.xxl,
  },
  emptyStateText: {
    ...TextStyles.body,
    color:     Colors.textMuted,
    textAlign: 'center',
    marginTop: Spacing.md,
  },

  // ── Loading indicator wrapper ─────────────────────────────────────────────────
  loadingWrapper: {
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'center',
    paddingVertical: Spacing.md,
    gap:             Spacing.sm,
  },
  loadingText: {
    ...TextStyles.bodySmall,
    color: Colors.textMuted,
  },
});

export default globalStyles;
