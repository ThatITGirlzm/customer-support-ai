import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { colors } from "../theme/colors";

const ITEMS = [
  { key: "home", label: "Home" },
  { key: "support", label: "Support" },
  { key: "safety", label: "Safety and limits" },
];

export function BottomNavigation({ activeScreen, onNavigate }) {
  return (
    <View style={styles.container} accessibilityLabel="Main navigation">
      {ITEMS.map((item) => {
        const selected = activeScreen === item.key;
        return (
          <Pressable
            key={item.key}
            accessible
            focusable
            accessibilityRole="button"
            accessibilityLabel={`${item.label}${selected ? ", current screen" : ""}`}
            accessibilityState={{ selected }}
            onPress={() => onNavigate(item.key)}
            style={({ pressed, focused }) => [
              styles.item,
              selected && styles.selected,
              pressed && styles.pressed,
              focused && styles.focused,
            ]}
          >
            <Text style={[styles.itemText, selected && styles.selectedText]}>{item.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 8,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  item: {
    flex: 1,
    minHeight: 54,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: "transparent",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 6,
    paddingVertical: 8,
  },
  selected: { backgroundColor: colors.mint, borderColor: colors.moss },
  pressed: { backgroundColor: colors.mint },
  focused: { borderColor: colors.focus, borderWidth: 3 },
  itemText: { color: colors.secondaryText, fontSize: 13, fontWeight: "600", textAlign: "center" },
  selectedText: { color: colors.moss, fontWeight: "800" },
});
