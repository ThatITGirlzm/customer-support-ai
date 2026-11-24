import React, { useCallback, useState } from "react";
import { StatusBar, StyleSheet, Text, View } from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { BottomNavigation } from "./src/components/BottomNavigation";
import { HomeScreen } from "./src/screens/HomeScreen";
import { SafetyScreen } from "./src/screens/SafetyScreen";
import { SupportScreen } from "./src/screens/SupportScreen";
import { colors } from "./src/theme/colors";

export default function App() {
  const [activeScreen, setActiveScreen] = useState("home");
  const [suggestedQuestion, setSuggestedQuestion] = useState("");

  function navigate(screen) {
    setSuggestedQuestion("");
    setActiveScreen(screen);
  }

  function chooseTopic(question) {
    setSuggestedQuestion(question);
    setActiveScreen("support");
  }

  const consumeSuggestion = useCallback(() => setSuggestedQuestion(""), []);

  let screen;
  if (activeScreen === "support") {
    screen = (
      <SupportScreen
        initialQuestion={suggestedQuestion}
        onSuggestionConsumed={consumeSuggestion}
      />
    );
  } else if (activeScreen === "safety") {
    screen = <SafetyScreen />;
  } else {
    screen = (
      <HomeScreen
        onStart={() => navigate("support")}
        onChooseTopic={chooseTopic}
        onOpenSafety={() => navigate("safety")}
      />
    );
  }

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.safeArea} edges={["top", "left", "right", "bottom"]}>
        <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
        <View style={styles.header}>
          <View style={styles.brandLine}>
            <Text accessibilityRole="header" style={styles.brand}>Averse</Text>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>SOURCE-LIMITED SUPPORT</Text>
            </View>
          </View>
          <Text style={styles.tagline}>Clear information. Honest limits.</Text>
        </View>
        <View style={styles.screen}>{screen}</View>
        <BottomNavigation activeScreen={activeScreen} onNavigate={navigate} />
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  header: { paddingHorizontal: 20, paddingTop: 10, paddingBottom: 12, gap: 4 },
  brandLine: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 10 },
  brand: { color: colors.moss, fontSize: 24, lineHeight: 30, fontWeight: "900" },
  badge: { backgroundColor: colors.lime, borderRadius: 10, paddingHorizontal: 9, paddingVertical: 5 },
  badgeText: { color: colors.text, fontSize: 11, lineHeight: 15, fontWeight: "800", letterSpacing: 0.5 },
  tagline: { color: colors.secondaryText, fontSize: 14, lineHeight: 20 },
  screen: { flex: 1 },
});
