import React from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { colors } from "../theme/colors";

export function AppButton({
  label,
  onPress,
  accessibilityHint,
  variant = "primary",
  disabled = false,
  style,
}) {
  const primary = variant === "primary";

  return (
    <Pressable
      accessible
      focusable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ disabled }}
      disabled={disabled}
      hitSlop={6}
      onPress={onPress}
      style={({ pressed, focused }) => [
        styles.button,
        primary ? styles.primary : styles.secondary,
        disabled && styles.disabled,
        pressed && !disabled && (primary ? styles.primaryPressed : styles.secondaryPressed),
        focused && (primary ? styles.focusedPrimary : styles.focusedSecondary),
        style,
      ]}
    >
      <Text style={[styles.label, primary ? styles.primaryLabel : styles.secondaryLabel]}>
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 54,
    borderRadius: 16,
    borderWidth: 2,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  primary: { backgroundColor: colors.moss, borderColor: colors.moss },
  secondary: { backgroundColor: colors.surface, borderColor: colors.border },
  primaryPressed: { backgroundColor: colors.mossPressed, borderColor: colors.mossPressed },
  secondaryPressed: { backgroundColor: colors.mint, borderColor: colors.moss },
  disabled: { backgroundColor: colors.disabled, borderColor: colors.disabled },
  focusedPrimary: { borderColor: colors.lime, borderWidth: 3 },
  focusedSecondary: { borderColor: colors.focus, borderWidth: 3 },
  label: { fontSize: 16, fontWeight: "700", textAlign: "center" },
  primaryLabel: { color: colors.surface },
  secondaryLabel: { color: colors.moss },
});
