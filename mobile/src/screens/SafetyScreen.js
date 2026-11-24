import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { colors } from "../theme/colors";

const LIMITS = [
  {
    title: "Approved sources only",
    text: "Averse uses approved source material. It may not cover your question, and the app will not fill gaps with invented facts or citations.",
  },
  {
    title: "Human assistance is not a handoff",
    text: "A response may say human help is needed. This mobile app does not contact a bank, regulator, support worker, or other person, and it cannot create an official complaint reference.",
  },
  {
    title: "No account access",
    text: "Averse cannot see or change accounts, transactions, payments, or identity records. Never enter passwords, PINs, one-time codes, full account numbers, or secrets.",
  },
  {
    title: "General information, not advice",
    text: "Averse provides limited general information. It does not give personal financial advice or decide what you should do with your money.",
  },
  {
    title: "Local demonstration only",
    text: "The backend demo route is disabled by default and is not available from this app. If separately enabled for local demonstration, it records to a local database only; it does not contact a bank, regulator, support worker, or phone.",
  },
];

export function SafetyScreen() {
  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View style={styles.intro}>
        <Text accessibilityRole="header" style={styles.title}>Safety and limitations</Text>
        <Text style={styles.body}>
          Use Averse for general information only. If you are at immediate risk, use a trusted official contact channel directly.
        </Text>
      </View>
      {LIMITS.map((item) => (
        <View key={item.title} style={styles.panel}>
          <Text accessibilityRole="header" style={styles.panelTitle}>{item.title}</Text>
          <Text style={styles.panelText}>{item.text}</Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 20, gap: 16, paddingBottom: 28 },
  intro: { gap: 10, marginBottom: 4 },
  title: { color: colors.text, fontSize: 28, lineHeight: 36, fontWeight: "800" },
  body: { color: colors.secondaryText, fontSize: 16, lineHeight: 24 },
  panel: {
    backgroundColor: colors.mint,
    borderColor: colors.moss,
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    gap: 8,
  },
  panelTitle: { color: colors.text, fontSize: 18, lineHeight: 25, fontWeight: "800" },
  panelText: { color: colors.text, fontSize: 15, lineHeight: 23 },
});
