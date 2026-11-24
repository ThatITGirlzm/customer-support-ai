/**
 * Styles for the Header component.
 *
 * The header sits at the top of every screen. It carries the app name,
 * an optional screen title, and navigation action buttons.
 */

import { StyleSheet, Platform } from 'react-native';
import Colors          from '../constants/colors';
import { Spacing }     from '../constants/spacing';
import { FontSize, FontWeight } from '../constants/typography';

const headerStyles = StyleSheet.create({

  // ── Outer container ──────────────────────────────────────────────────────────
  container: {
    backgroundColor: Colors.headerBg,
    paddingTop:      Platform.OS === 'ios' ? 0 : Spacing.sm,  // SafeAreaView handles iOS inset
    paddingBottom:   Spacing.sm,
    paddingHorizontal: Spacing.md,
  },

  // ── Inner row ────────────────────────────────────────────────────────────────
  inner: {
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'space-between',
    minHeight:      48,
  },

  // ── Left slot (back button or brand) ──────────────────────────────────────────
  leftSlot: {
    flex:           1,
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'flex-start',
  },

  // ���─ Centre slot (title) ───────────────────────────────────────────────────────
  centreSlot: {
    flex:           2,
    alignItems:     'center',
    justifyContent: 'center',
  },

  // ── Right slot (action buttons) ───────────────────────────────────────────────
  rightSlot: {
    flex:           1,
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'flex-end',
    gap:            Spacing.xs,
  },

  // ── Branding (home header) ────────────────────────────────────────────────────
  brandRow: {
    flexDirection: 'row',
    alignItems:    'center',
    gap:           Spacing.xs,
  },
  brandMark: {
    width:           32,
    height:          32,
    borderRadius:    8,
    backgroundColor: Colors.white,
    alignItems:      'center',
    justifyContent:  'center',
  },
  brandMarkText: {
    fontSize:   FontSize.md,
    fontWeight: FontWeight.bold,
    color:      Colors.primary,
  },
  brandName: {
    fontSize:   FontSize.lg,
    fontWeight: FontWeight.bold,
    color:      Colors.white,
    letterSpacing: 0.5,
  },
  brandTagline: {
    fontSize: FontSize.xs,
    color:    'rgba(255,255,255,0.75)',
    marginTop: 1,
  },

  // ── Screen title (non-home screens) ──────────────────────────────────────────
  screenTitle: {
    fontSize:   FontSize.md,
    fontWeight: FontWeight.semiBold,
    color:      Colors.white,
    textAlign:  'center',
  },

  // ── Icon button (back / action) ───────────────────────────────────────────────
  iconBtn: {
    width:          40,
    height:         40,
    borderRadius:   20,
    alignItems:     'center',
    justifyContent: 'center',
  },
  iconBtnPressed: {
    backgroundColor: 'rgba(255,255,255,0.15)',
  },

  // ── Back button label (text fallback when no icon font) ──────────────────────
  backLabel: {
    fontSize:   FontSize.base,
    color:      Colors.white,
    fontWeight: FontWeight.medium,
  },

  // ── Separator below header ────────────────────────────────────────────────────
  shadow: {
    shadowColor:   '#000',
    shadowOffset:  { width: 0, height: 2 },
    shadowOpacity: 0.18,
    shadowRadius:  4,
    elevation:     4,
  },
});

export default headerStyles;
