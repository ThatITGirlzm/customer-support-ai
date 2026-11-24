/**
 * AboutScreen
 *
 * Displays app description, data-source information, disclaimer, and a live
 * health-check button that pings GET /health on the backend.
 *
 * Layout:
 *   Header (screen mode, back button)
 *   ↓ ScrollView
 *       About section
 *       Data sources section
 *       Backend status section  (health check button + result)
 *       Disclaimer section
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  ActivityIndicator,
  StyleSheet,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import Colors       from '../constants/colors';
import Strings      from '../constants/strings';
import { Spacing, Radius, Shadow } from '../constants/spacing';
import { FontSize, FontWeight } from '../constants/typography';
import globalStyles from '../styles/globalStyles';
import Header       from '../components/Header';
import { getHealth } from '../api/endpoints';

// ── Section block ─────────────────────────────────────────────────────────────

function Section({ heading, children }) {
  return (
    <View style={localStyles.section}>
      <Text style={localStyles.sectionHeading}>{heading}</Text>
      {children}
    </View>
  );
}

// ── Screen ────────────────────────────────────────────────────────────────────

export default function AboutScreen({ navigation }) {
  const [healthStatus, setHealthStatus] = useState(null);  // null | 'ok' | 'fail'
  const [checking,     setChecking]     = useState(false);

  const checkHealth = useCallback(async () => {
    setChecking(true);
    setHealthStatus(null);
    try {
      const data = await getHealth();
      setHealthStatus(data?.status === 'ok' ? 'ok' : 'fail');
    } catch {
      setHealthStatus('fail');
    } finally {
      setChecking(false);
    }
  }, []);

  return (
    <SafeAreaView style={globalStyles.screen} edges={['bottom']}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.headerBg} />

      {/* Header */}
      <Header
        mode="screen"
        title={Strings.navAbout}
        onBack={() => navigation.goBack()}
      />

      <ScrollView
        contentContainerStyle={localStyles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* ── About ──────────────────────────────────────────────────────── */}
        <Section heading={Strings.aboutHeading}>
          <Text style={localStyles.versionLabel}>{Strings.aboutVersion}</Text>
          <Text style={localStyles.bodyText}>{Strings.aboutBody}</Text>
        </Section>

        <View style={globalStyles.divider} />

        {/* ── Data sources ───────────────────────────────────────────────── */}
        <Section heading={Strings.aboutDataHeading}>
          <Text style={localStyles.bodyText}>{Strings.aboutDataBody}</Text>
        </Section>

        <View style={globalStyles.divider} />

        {/* ── Backend status ─────────────────────────────────────────────── */}
        <Section heading={Strings.aboutBackendHeading}>
          <Pressable
            onPress={checkHealth}
            disabled={checking}
            style={({ pressed }) => [
              localStyles.healthBtn,
              pressed && localStyles.healthBtnPressed,
              checking && globalStyles.btnDisabled,
            ]}
            accessibilityRole="button"
            accessibilityLabel={Strings.aboutCheckHealth}
          >
            {checking
              ? <ActivityIndicator size="small" color={Colors.white} />
              : <Text style={localStyles.healthBtnText}>{Strings.aboutCheckHealth}</Text>
            }
          </Pressable>

          {healthStatus === 'ok' && (
            <View style={[localStyles.healthResult, localStyles.healthResultOk]}>
              <Text style={localStyles.healthResultText}>{Strings.aboutHealthOk}</Text>
            </View>
          )}
          {healthStatus === 'fail' && (
            <View style={[localStyles.healthResult, localStyles.healthResultFail]}>
              <Text style={localStyles.healthResultText}>{Strings.aboutHealthFail}</Text>
            </View>
          )}
        </Section>

        <View style={globalStyles.divider} />

        {/* ── Disclaimer ─────────────────────────────────────────────────── */}
        <Section heading={Strings.aboutDisclaimerHeading}>
          <View style={localStyles.disclaimerBox}>
            <Text style={localStyles.disclaimerText}>{Strings.aboutDisclaimerBody}</Text>
          </View>
        </Section>

        <View style={{ height: Spacing.xxl }} />
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Local styles ───────────────────────────────────────────────────────────────

const localStyles = StyleSheet.create({
  scrollContent: {
    paddingHorizontal: Spacing.md,
    paddingTop:        Spacing.lg,
    paddingBottom:     Spacing.xxl,
  },

  section: {
    marginBottom: Spacing.md,
  },
  sectionHeading: {
    fontSize:     FontSize.lg,
    fontWeight:   FontWeight.bold,
    color:        Colors.textPrimary,
    marginBottom: Spacing.sm,
  },
  versionLabel: {
    fontSize:     FontSize.sm,
    color:        Colors.textMuted,
    marginBottom: Spacing.sm,
    fontStyle:    'italic',
  },
  bodyText: {
    fontSize:   FontSize.base,
    color:      Colors.textSecondary,
    lineHeight: FontSize.base * 1.65,
  },

  // Health check
  healthBtn: {
    backgroundColor: Colors.primary,
    borderRadius:    Radius.pill,
    paddingVertical:   Spacing.sm + 2,
    paddingHorizontal: Spacing.lg,
    alignSelf:       'flex-start',
    alignItems:      'center',
    justifyContent:  'center',
    minWidth:        160,
    marginBottom:    Spacing.sm,
    ...Shadow.sm,
  },
  healthBtnPressed: {
    opacity: 0.85,
  },
  healthBtnText: {
    fontSize:   FontSize.base,
    fontWeight: FontWeight.semiBold,
    color:      Colors.white,
  },
  healthResult: {
    borderRadius:    Radius.md,
    paddingVertical:   Spacing.sm,
    paddingHorizontal: Spacing.md,
    marginTop:       Spacing.xs,
    alignSelf:       'flex-start',
  },
  healthResultOk: {
    backgroundColor: Colors.actionAnswer + '22',
  },
  healthResultFail: {
    backgroundColor: Colors.actionBlock + '22',
  },
  healthResultText: {
    fontSize:   FontSize.sm,
    fontWeight: FontWeight.semiBold,
    color:      Colors.textPrimary,
  },

  // Disclaimer
  disclaimerBox: {
    backgroundColor: Colors.actionAbstain + '18',
    borderLeftWidth:  3,
    borderLeftColor:  Colors.actionAbstain,
    borderRadius:     Radius.sm,
    padding:          Spacing.md,
  },
  disclaimerText: {
    fontSize:   FontSize.sm,
    color:      Colors.textSecondary,
    lineHeight: FontSize.sm * 1.65,
  },
});
