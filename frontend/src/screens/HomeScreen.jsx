/**
 * HomeScreen
 *
 * Landing screen. Shows the app brand, a short description, suggested
 * questions the user can tap to pre-fill, and a primary CTA that navigates
 * to ChatScreen.
 *
 * Layout (scroll-safe):
 *   Header (home mode)
 *   ↓ Hero section — heading + sub-heading
 *   ↓ CTA button — "Start a Conversation"
 *   ↓ Suggested questions list
 */

import React, { useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import Colors       from '../constants/colors';
import Strings      from '../constants/strings';
import { Spacing }  from '../constants/spacing';
import globalStyles from '../styles/globalStyles';
import Header       from '../components/Header';

// ── Suggested question card ───────────────────────────────────────────────────

function SuggestionCard({ text, onPress }) {
  return (
    <Pressable
      onPress={() => onPress(text)}
      style={({ pressed }) => [
        styles.suggestionCard,
        pressed && styles.suggestionCardPressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`Ask: ${text}`}
    >
      <Text style={styles.suggestionArrow}>›</Text>
      <Text style={styles.suggestionText}>{text}</Text>
    </Pressable>
  );
}

// ── Screen ────────────────────────────────────────────────────────────────────

export default function HomeScreen({ navigation }) {
  // Navigate to chat with an optional pre-filled question.
  const goToChat = useCallback((initialQuestion = '') => {
    navigation.navigate('Chat', { initialQuestion });
  }, [navigation]);

  const goToAbout = useCallback(() => {
    navigation.navigate('About');
  }, [navigation]);

  // Right slot for the header — "About" text button.
  const headerRight = (
    <Pressable
      onPress={goToAbout}
      style={({ pressed }) => [
        headerRightStyle.btn,
        pressed && headerRightStyle.btnPressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel="About Averse"
    >
      <Text style={headerRightStyle.label}>About</Text>
    </Pressable>
  );

  return (
    <SafeAreaView style={globalStyles.screen} edges={['bottom']}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.headerBg} />

      {/* Header */}
      <Header mode="home" rightElement={headerRight} />

      {/* Scrollable body */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* ── Hero ─────────────────────────────────────────────────────── */}
        <View style={styles.hero}>
          <Text style={styles.heroHeading}>{Strings.homeHeading}</Text>
          <Text style={styles.heroSubheading}>{Strings.homeSubheading}</Text>
        </View>

        {/* ── CTA ──────────────────────────────────────────────────────── */}
        <Pressable
          onPress={() => goToChat()}
          style={({ pressed }) => [
            globalStyles.btnPrimary,
            styles.ctaBtn,
            pressed && styles.ctaBtnPressed,
          ]}
          accessibilityRole="button"
        >
          <Text style={globalStyles.btnPrimaryText}>{Strings.homeStartBtn}</Text>
        </Pressable>

        <Text style={styles.promptHint}>{Strings.homePromptHint}</Text>

        {/* ── Divider ──────────────────────────────────────────────────── */}
        <View style={globalStyles.divider} />

        {/* ── Suggested questions ──────────────────────────────────────── */}
        <Text style={styles.suggestionsHeading}>
          {Strings.homeSuggestionsHeading}
        </Text>

        {Strings.homeSuggestions.map((q, i) => (
          <SuggestionCard key={i} text={q} onPress={goToChat} />
        ))}

        {/* Bottom breathing room */}
        <View style={{ height: Spacing.xxl }} />
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Local styles ──────────────────────────────────────────────────────────────
// (layout only — colours and typography come from globalStyles / constants)

import { StyleSheet } from 'react-native';
import { Radius, Shadow } from '../constants/spacing';
import { FontSize, FontWeight } from '../constants/typography';

const styles = StyleSheet.create({
  scrollContent: {
    paddingHorizontal: Spacing.md,
    paddingTop:        Spacing.xl,
    paddingBottom:     Spacing.xxl,
  },

  // Hero
  hero: {
    marginBottom: Spacing.lg,
  },
  heroHeading: {
    fontSize:     FontSize.xxl,
    fontWeight:   FontWeight.bold,
    color:        Colors.textPrimary,
    lineHeight:   FontSize.xxl * 1.2,
    marginBottom: Spacing.sm,
  },
  heroSubheading: {
    fontSize:   FontSize.base,
    color:      Colors.textSecondary,
    lineHeight: FontSize.base * 1.6,
  },

  // CTA
  ctaBtn: {
    marginBottom: Spacing.sm,
  },
  ctaBtnPressed: {
    opacity: 0.85,
  },

  // Hint below CTA
  promptHint: {
    fontSize:     FontSize.sm,
    color:        Colors.textMuted,
    textAlign:    'center',
    marginBottom: Spacing.lg,
    fontStyle:    'italic',
  },

  // Suggestions
  suggestionsHeading: {
    fontSize:     FontSize.sm,
    fontWeight:   FontWeight.semiBold,
    color:        Colors.textSecondary,
    marginBottom: Spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  suggestionCard: {
    flexDirection:   'row',
    alignItems:      'center',
    backgroundColor: Colors.cardBg,
    borderRadius:    Radius.md,
    borderWidth:     1,
    borderColor:     Colors.border,
    paddingHorizontal: Spacing.md,
    paddingVertical:   Spacing.sm + 2,
    marginBottom:    Spacing.sm,
    gap:             Spacing.sm,
    ...Shadow.sm,
  },
  suggestionCardPressed: {
    backgroundColor: Colors.surfaceLight,
  },
  suggestionArrow: {
    fontSize:   FontSize.lg,
    color:      Colors.primary,
    fontWeight: FontWeight.bold,
    lineHeight: FontSize.lg * 1.2,
  },
  suggestionText: {
    flex:       1,
    fontSize:   FontSize.base,
    color:      Colors.textPrimary,
    lineHeight: FontSize.base * 1.5,
  },
});

// Header right-slot button styles (defined outside main StyleSheet to avoid
// circular reference with the headerStyles import chain).
const headerRightStyle = StyleSheet.create({
  btn: {
    paddingHorizontal: Spacing.sm,
    paddingVertical:   Spacing.xs,
    borderRadius:      Radius.sm,
  },
  btnPressed: {
    backgroundColor: 'rgba(255,255,255,0.15)',
  },
  label: {
    fontSize:   FontSize.base,
    color:      Colors.white,
    fontWeight: FontWeight.medium,
  },
});
