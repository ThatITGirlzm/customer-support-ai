import React, { useEffect } from "react";
import { AccessibilityInfo, Platform, StyleSheet, Text, View } from "react-native";
import { colors } from "../theme/colors";

const PRESENTATION = {
  ABSTAIN_NOT_IN_SOURCES: {
    title: "No supported answer",
    explanation: (reason) => {
      if (reason === "AMBIGUOUS_SENSITIVE_REQUEST") {
        return "Averse could not tell whether this concerns an active sensitive situation. No referral was sent.";
      }
      if (reason === "SENSITIVE_INTENT_POLICY_PENDING") {
        return "There is no approved answer or referral rule for this classifier result. No referral was sent.";
      }
      if (reason === "NO_APPROVED_ANSWER_RULE") {
        return "A retrieved passage or score is not enough to authorize an answer. No reviewed answer rule covers this request.";
      }
      return "Averse could not find an approved answer for this request, so the app has not added facts or citations.";
    },
    style: "neutral",
  },
  BLOCK_INJECTION: {
    title: "Safety block",
    explanation: () => "The request was stopped because it asks the service to bypass its safety or source rules.",
    style: "safety",
  },
  REFER_HUMAN: {
    title: "Human assistance needed",
    explanation: () =>
      "Averse identified a need for human assistance. This app did not send a referral or create an official complaint reference.",
    style: "safety",
  },
  INVALID_REQUEST: {
    title: "Request not accepted",
    explanation: () => "The service could not process this request as submitted. Rephrase it without personal credentials.",
    style: "neutral",
  },
  SERVICE_UNAVAILABLE: {
    title: "Service unavailable",
    explanation: (reason) => {
      if (reason === "UNSUPPORTED_RESPONSE_TYPE") {
        return "This app hides response types outside its approved interface. No factual answer or citation was displayed.";
      }
      if (reason === "CLIENT_REQUEST_TIMEOUT") {
        return "The service did not respond before the app's wait limit. No automatic retry was made.";
      }
      return "Averse could not process this request right now. Please try again later.";
    },
    style: "neutral",
  },
};

export function ActionResponse({ result }) {
  const presentation = result ? PRESENTATION[result.action] : null;
  const title =
    result?.reasonCode === "UNSUPPORTED_RESPONSE_TYPE" ? "Response not shown" : presentation?.title;
  const explanation = presentation ? presentation.explanation(result.reasonCode) : "";

  useEffect(() => {
    if (!result || !presentation || Platform.OS !== "ios") return;
    AccessibilityInfo.announceForAccessibility(
      `${title}. ${result.responseText}. Why this response? ${explanation}`,
    );
  }, [result, presentation, title, explanation]);

  if (!result || !presentation) return null;

  const panelStyle = presentation.style === "safety" ? styles.safety : styles.neutral;

  return (
    <View
      accessibilityLiveRegion="polite"
      style={[styles.panel, panelStyle]}
    >
      <Text accessibilityRole="header" style={styles.title}>
        {title}
      </Text>
      <Text style={styles.responseText}>{result.responseText}</Text>
      <Text style={styles.whyTitle}>Why this response?</Text>
      <Text style={styles.explanation}>{explanation}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  panel: { borderRadius: 18, borderWidth: 1.5, padding: 18, gap: 10 },
  neutral: { backgroundColor: colors.mint, borderColor: colors.moss },
  safety: { backgroundColor: colors.sand, borderColor: colors.sandBorder },
  title: { color: colors.text, fontSize: 19, lineHeight: 26, fontWeight: "800" },
  responseText: { color: colors.text, fontSize: 16, lineHeight: 24 },
  whyTitle: { color: colors.text, fontSize: 15, lineHeight: 21, fontWeight: "800", marginTop: 4 },
  explanation: { color: colors.text, fontSize: 15, lineHeight: 23 },
});
