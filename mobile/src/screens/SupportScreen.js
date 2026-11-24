import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { AppButton } from "../components/AppButton";
import { sendQuestion, UnsupportedResponseError } from "../api/client";
import { colors } from "../theme/colors";
import { ActionResponse } from "./ActionResponse";

const GENERIC_UNAVAILABLE = {
  action: "SERVICE_UNAVAILABLE",
  responseText: "Averse is unavailable right now. Please try again later.",
  reasonCode: "CLIENT_CONNECTION_UNAVAILABLE",
};

export function SupportScreen({ initialQuestion = "", onSuggestionConsumed }) {
  const [question, setQuestion] = useState(initialQuestion);
  const [result, setResult] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);
  const abortRef = useRef(null);
  const sendingRef = useRef(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (initialQuestion) {
      setQuestion(initialQuestion);
      onSuggestionConsumed?.();
    }
  }, [initialQuestion, onSuggestionConsumed]);

  async function submit() {
    const submittedQuestion = question.trim();
    if (!submittedQuestion || sendingRef.current) return;

    const controller = new AbortController();
    abortRef.current = controller;
    sendingRef.current = true;
    setIsSending(true);
    setQuestion("");
    setResult(null);
    const timeout = setTimeout(() => controller.abort(), 25000);

    try {
      const nextResult = await sendQuestion(submittedQuestion, controller.signal);
      if (mountedRef.current) setResult(nextResult);
    } catch (error) {
      if (!mountedRef.current) return;
      if (error instanceof UnsupportedResponseError) {
        setResult({
          action: "SERVICE_UNAVAILABLE",
          responseText: "This response type is not available in the mobile app. No answer was shown.",
          reasonCode: "UNSUPPORTED_RESPONSE_TYPE",
        });
      } else if (controller.signal.aborted) {
        setResult({
          action: "SERVICE_UNAVAILABLE",
          responseText: "Averse did not respond in time. Please try again later.",
          reasonCode: "CLIENT_REQUEST_TIMEOUT",
        });
      } else {
        setResult(GENERIC_UNAVAILABLE);
      }
    } finally {
      clearTimeout(timeout);
      abortRef.current = null;
      sendingRef.current = false;
      if (mountedRef.current) setIsSending(false);
    }
  }

  const canSend = question.trim().length > 0 && !isSending;

  return (
    <KeyboardAvoidingView
      style={styles.keyboardRoot}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.intro}>
          <Text accessibilityRole="header" style={styles.title}>Ask Averse</Text>
          <Text style={styles.body}>
            Ask a general question about approved source information. Averse may not have a reviewed answer.
          </Text>
        </View>

        <View style={styles.warning}>
          <Text accessibilityRole="header" style={styles.warningTitle}>Do not share secrets</Text>
          <Text style={styles.warningText}>
            Never enter a password, PIN, one-time code, full account number, or other sensitive credential.
          </Text>
        </View>

        <View style={styles.inputGroup}>
          <Text nativeID="question-label" style={styles.inputLabel}>Your question</Text>
          <TextInput
            accessibilityLabel="Your question"
            accessibilityHint="Enter a general question. Do not include passwords, PINs, one-time codes, or account numbers."
            accessibilityLabelledBy={Platform.OS === "android" ? "question-label" : undefined}
            value={question}
            onChangeText={setQuestion}
            onFocus={() => setInputFocused(true)}
            onBlur={() => setInputFocused(false)}
            placeholder="Type a general question"
            placeholderTextColor={colors.secondaryText}
            multiline
            textAlignVertical="top"
            autoCorrect
            autoCapitalize="sentences"
            returnKeyType="default"
            editable={!isSending}
            style={[styles.input, inputFocused && styles.inputFocused]}
          />
          <Text style={styles.inputHelp}>Only the current question is sent. The app does not save question history.</Text>
        </View>

        <AppButton
          label={isSending ? "Sending question…" : "Send question"}
          accessibilityHint="Sends this question to the approved Averse support endpoint."
          onPress={submit}
          disabled={!canSend}
        />

        {isSending ? (
          <View accessible accessibilityRole="text" accessibilityLabel="Sending question" style={styles.progress}>
            <ActivityIndicator color={colors.moss} />
            <Text style={styles.progressText}>Sending question to Averse…</Text>
          </View>
        ) : null}

        <ActionResponse result={result} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  keyboardRoot: { flex: 1 },
  content: { padding: 20, gap: 20, paddingBottom: 28 },
  intro: { gap: 10, paddingTop: 4 },
  title: { color: colors.text, fontSize: 28, lineHeight: 36, fontWeight: "800" },
  body: { color: colors.secondaryText, fontSize: 16, lineHeight: 24 },
  warning: {
    backgroundColor: colors.sand,
    borderColor: colors.sandBorder,
    borderWidth: 1.5,
    borderRadius: 18,
    padding: 16,
    gap: 8,
  },
  warningTitle: { color: colors.text, fontSize: 17, lineHeight: 24, fontWeight: "800" },
  warningText: { color: colors.text, fontSize: 15, lineHeight: 23 },
  inputGroup: { gap: 9 },
  inputLabel: { color: colors.text, fontSize: 16, lineHeight: 23, fontWeight: "700" },
  input: {
    minHeight: 136,
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: 16,
    padding: 14,
    backgroundColor: colors.surface,
    color: colors.text,
    fontSize: 17,
    lineHeight: 25,
  },
  inputFocused: { borderColor: colors.focus, borderWidth: 3 },
  inputHelp: { color: colors.secondaryText, fontSize: 14, lineHeight: 21 },
  progress: { minHeight: 48, flexDirection: "row", alignItems: "center", gap: 12 },
  progressText: { flex: 1, color: colors.text, fontSize: 15, lineHeight: 22 },
});
