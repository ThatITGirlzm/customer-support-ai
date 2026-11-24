import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { AppButton } from "../components/AppButton";
import { colors } from "../theme/colors";

const TOPICS = [
  { label: "Complaints", question: "What approved information is available about the complaints process?" },
  { label: "Consumer rights", question: "What approved information is available about consumer rights?" },
  { label: "Payments and mobile money", question: "What approved information is available about payments and mobile money?" },
  { label: "Financial education", question: "What approved financial education information is available?" },
];

export function HomeScreen({ onStart, onChooseTopic, onOpenSafety }) {
  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View style={styles.intro}>
        <Text accessibilityRole="header" style={styles.title}>
          Support within clear limits
        </Text>
        <Text style={styles.body}>
          Averse uses approved source material to provide general guidance. It may not have an
          answer. It cannot access accounts, make payments, or give personal financial advice.
        </Text>
      </View>

      <View style={styles.topicSection}>
        <Text accessibilityRole="header" style={styles.sectionTitle}>
          Choose a topic
        </Text>
        <Text style={styles.helper}>
          Each shortcut starts a question you can edit before sending.
        </Text>
        <View style={styles.topicList}>
          {TOPICS.map((topic) => (
            <AppButton
              key={topic.label}
              variant="secondary"
              label={topic.label}
              accessibilityHint="Opens Support with an editable suggested question. It will not be sent automatically."
              onPress={() => onChooseTopic(topic.question)}
              style={styles.topicButton}
            />
          ))}
        </View>
      </View>

      <View style={styles.safetyPanel}>
        <Text accessibilityRole="header" style={styles.panelTitle}>
          Keep your details safe
        </Text>
        <Text style={styles.panelText}>
          Never enter a password, PIN, one-time code, full account number, or other secret. Averse
          cannot access your account or submit a real complaint.
        </Text>
        <AppButton
          variant="secondary"
          label="Read safety and limitations"
          accessibilityHint="Explains what Averse can and cannot do."
          onPress={onOpenSafety}
          style={styles.safetyButton}
        />
      </View>

      <AppButton
        label="Start a support question"
        accessibilityHint="Opens the support screen. Nothing is sent until you choose Send."
        onPress={() => onStart("")}
      />
      <Text style={styles.footerNote}>Source-limited support. No account access or financial advice.</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 20, gap: 24, paddingBottom: 28 },
  intro: { gap: 12, paddingTop: 4 },
  title: { color: colors.text, fontSize: 30, lineHeight: 38, fontWeight: "800" },
  body: { color: colors.secondaryText, fontSize: 17, lineHeight: 26 },
  topicSection: { gap: 12 },
  sectionTitle: { color: colors.text, fontSize: 21, lineHeight: 28, fontWeight: "700" },
  helper: { color: colors.secondaryText, fontSize: 15, lineHeight: 22 },
  topicList: { gap: 10 },
  topicButton: { alignItems: "flex-start" },
  safetyPanel: {
    backgroundColor: colors.sand,
    borderColor: colors.sandBorder,
    borderWidth: 1.5,
    borderRadius: 20,
    padding: 18,
    gap: 12,
  },
  panelTitle: { color: colors.text, fontSize: 19, lineHeight: 25, fontWeight: "800" },
  panelText: { color: colors.text, fontSize: 16, lineHeight: 24 },
  safetyButton: { alignSelf: "stretch" },
  footerNote: { color: colors.secondaryText, fontSize: 14, lineHeight: 21, textAlign: "center" },
});
