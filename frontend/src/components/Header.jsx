/**
 * Header
 *
 * App-wide header bar. Two display modes:
 *
 *   mode="home"  — shows the Averse brand mark + name + tagline in the left
 *                  slot, and an optional right action (e.g. About icon).
 *
 *   mode="screen" — shows an optional back button in the left slot, the
 *                   screen title centred, and optional right actions.
 *
 * Props:
 *   mode         {'home'|'screen'}  default 'screen'
 *   title        {string}           screen title (mode='screen')
 *   onBack       {function}         called when the back button is pressed
 *   showBack     {boolean}          show back button (default true in screen mode)
 *   rightElement {ReactNode}        anything to render in the right slot
 */

import React, { useCallback } from 'react';
import { View, Text, Pressable } from 'react-native';
import { SafeAreaView }          from 'react-native-safe-area-context';

import headerStyles from '../styles/headerStyles';

export default function Header({
  mode        = 'screen',
  title       = '',
  onBack,
  showBack    = true,
  rightElement,
}) {
  const handleBack = useCallback(() => {
    if (onBack) onBack();
  }, [onBack]);

  return (
    <SafeAreaView edges={['top']} style={[headerStyles.container, headerStyles.shadow]}>
      <View style={headerStyles.inner}>

        {/* ── Left slot ──────────────────────────────────────────────────── */}
        <View style={headerStyles.leftSlot}>
          {mode === 'home' ? (
            <View style={headerStyles.brandRow}>
              <View style={headerStyles.brandMark}>
                <Text style={headerStyles.brandMarkText}>A</Text>
              </View>
              <View>
                <Text style={headerStyles.brandName}>Averse</Text>
                <Text style={headerStyles.brandTagline}>Consumer Finance Assistant</Text>
              </View>
            </View>
          ) : (
            showBack && onBack ? (
              <Pressable
                onPress={handleBack}
                style={({ pressed }) => [
                  headerStyles.iconBtn,
                  pressed && headerStyles.iconBtnPressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Go back"
              >
                <Text style={headerStyles.backLabel}>{'‹'}</Text>
              </Pressable>
            ) : null
          )}
        </View>

        {/* ── Centre slot ────────────────────────────────────────────────── */}
        <View style={headerStyles.centreSlot}>
          {mode === 'screen' && title ? (
            <Text style={headerStyles.screenTitle} numberOfLines={1}>
              {title}
            </Text>
          ) : null}
        </View>

        {/* ── Right slot ─────────────────────────────────────────────────── */}
        <View style={headerStyles.rightSlot}>
          {rightElement ?? null}
        </View>

      </View>
    </SafeAreaView>
  );
}
