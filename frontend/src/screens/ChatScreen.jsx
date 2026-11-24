/**
 * ChatScreen
 *
 * Full-screen conversational interface. Sends questions to the Averse backend
 * and renders each turn as a MessageBubble.
 *
 * State:
 *   messages  — array of { id, role, text?, response?, timestamp }
 *   input     — current composer text
 *   loading   — true while awaiting a backend response
 *   error     — ApiError or null
 *
 * Navigation param:
 *   initialQuestion {string} — optional question to pre-fill from HomeScreen
 */

import React, {
  useState,
  useRef,
  useEffect,
  useCallback,
  useMemo,
} from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  Pressable,
  Keyboard,
  Alert,
  ActivityIndicator,
  StyleSheet,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import Colors       from '../constants/colors';
import Strings      from '../constants/strings';
import { Spacing, Radius } from '../constants/spacing';
import { FontSize, FontWeight } from '../constants/typography';

import chatStyles   from '../styles/chatStyles';
import globalStyles from '../styles/globalStyles';

import Header        from '../components/Header';
import MessageBubble from '../components/MessageBubble';

import { postQuestion } from '../api/endpoints';

const MAX_CHARS = 2000;

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function userMessage(text) {
  return { id: makeId(), role: 'user', text, timestamp: new Date() };
}

function botMessage(response) {
  return { id: makeId(), role: 'bot', response, timestamp: new Date() };
}

// ── New-conversation header button ────────────────────────────────────────────

function ClearButton({ onPress }) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        localStyles.clearBtn,
        pressed && localStyles.clearBtnPressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={Strings.chatNewConversation}
    >
      <Text style={localStyles.clearBtnText}>✕ New</Text>
    </Pressable>
  );
}

// ── Typing indicator ──────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <View style={chatStyles.typingRow}>
      <View style={chatStyles.typingBubble}>
        <View style={chatStyles.typingDot} />
        <View style={chatStyles.typingDot} />
        <View style={chatStyles.typingDot} />
        <Text style={chatStyles.typingLabel}>{Strings.chatThinking}</Text>
      </View>
    </View>
  );
}

// ── Screen ────────────────────────────────────────────────────────────────────

export default function ChatScreen({ route, navigation }) {
  const initialQuestion = route?.params?.initialQuestion ?? '';

  const [messages, setMessages] = useState([]);
  const [input,    setInput]    = useState(initialQuestion);
  const [loading,  setLoading]  = useState(false);
  const [focused,  setFocused]  = useState(false);

  const listRef    = useRef(null);
  const inputRef   = useRef(null);

  // Pre-fill and auto-send if an initial question was passed in.
  useEffect(() => {
    if (initialQuestion.trim()) {
      setInput(initialQuestion);
    }
  }, [initialQuestion]);

  // Scroll to bottom whenever the messages array changes.
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        listRef.current?.scrollToEnd({ animated: true });
      }, 80);
    }
  }, [messages, loading]);

  // ── Send ────────────────────────────────────────────────────────────────────
  const handleSend = useCallback(async () => {
    const question = input.trim();

    if (!question) {
      Alert.alert('', Strings.errorEmptyQuestion);
      return;
    }
    if (question.length > MAX_CHARS) {
      Alert.alert('', Strings.errorQuestionTooLong);
      return;
    }

    Keyboard.dismiss();
    setInput('');
    setLoading(true);

    // Append user turn immediately.
    setMessages(prev => [...prev, userMessage(question)]);

    try {
      const response = await postQuestion(question);
      setMessages(prev => [...prev, botMessage(response)]);
    } catch (err) {
      Alert.alert(
        Strings.errorNetworkTitle,
        err?.message ?? Strings.errorNetworkMsg,
      );
      // Remove the user message on hard failure so the state stays consistent.
      setMessages(prev => prev.slice(0, -1));
      setInput(question); // restore so the user can retry
    } finally {
      setLoading(false);
    }
  }, [input]);

  // ── Clear conversation ──────────────────────────────────────────────────────
  const handleClear = useCallback(() => {
    if (messages.length === 0) return;
    Alert.alert(
      Strings.chatClearConfirmTitle,
      Strings.chatClearConfirmMsg,
      [
        { text: Strings.chatClearConfirmCancel, style: 'cancel' },
        {
          text:    Strings.chatClearConfirmOk,
          style:   'destructive',
          onPress: () => setMessages([]),
        },
      ],
    );
  }, [messages.length]);

  // ── Character count colour ──────────────────────────────────────────────────
  const remaining = MAX_CHARS - input.length;
  const charCountStyle = remaining < 200
    ? [localStyles.charCount, localStyles.charCountWarn]
    : localStyles.charCount;

  // ── FlatList render item ────────────────────────────────────────────────────
  const renderItem = useCallback(({ item, index }) => (
    <MessageBubble
      message={item}
      isLast={index === messages.length - 1}
    />
  ), [messages.length]);

  const keyExtractor = useCallback(item => item.id, []);

  const listData = useMemo(() => messages, [messages]);

  // ── Header right element ────────────────────────────────────────────────────
  const headerRight = messages.length > 0
    ? <ClearButton onPress={handleClear} />
    : null;

  return (
    <SafeAreaView style={chatStyles.screen} edges={['bottom']}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.headerBg} />

      {/* Header */}
      <Header
        mode="screen"
        title={Strings.navChat}
        onBack={() => navigation.goBack()}
        rightElement={headerRight}
      />

      {/* Message list */}
      <FlatList
        ref={listRef}
        data={listData}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        style={chatStyles.messageList}
        contentContainerStyle={[
          chatStyles.messageListContent,
          messages.length === 0 && { flex: 1 },
        ]}
        keyboardShouldPersistTaps="handled"
        ListEmptyComponent={
          <View style={chatStyles.emptyWrapper}>
            <Text style={chatStyles.emptyIcon}>💬</Text>
            <Text style={chatStyles.emptyText}>{Strings.chatEmptyHint}</Text>
          </View>
        }
        ListFooterComponent={loading ? <TypingIndicator /> : null}
      />

      {/* Composer bar */}
      <View style={chatStyles.composerBar}>
        <View style={{ flex: 1 }}>
          {/* Character count (only shown when user has typed something) */}
          {input.length > 0 && (
            <Text style={charCountStyle}>{remaining} remaining</Text>
          )}
          <View style={[
            chatStyles.inputWrapper,
            focused && chatStyles.inputWrapperFocused,
          ]}>
            <TextInput
              ref={inputRef}
              style={chatStyles.input}
              value={input}
              onChangeText={setInput}
              placeholder={Strings.chatPlaceholder}
              placeholderTextColor={Colors.textMuted}
              multiline
              maxLength={MAX_CHARS + 50}  // soft warn before hard block
              returnKeyType="send"
              blurOnSubmit={false}
              onSubmitEditing={handleSend}
              onFocus={() => setFocused(true)}
              onBlur={()  => setFocused(false)}
              editable={!loading}
              accessibilityLabel="Question input"
            />
          </View>
        </View>

        {/* Send button */}
        <Pressable
          onPress={handleSend}
          disabled={loading || input.trim().length === 0}
          style={[
            chatStyles.sendBtn,
            (loading || input.trim().length === 0) && chatStyles.sendBtnDisabled,
          ]}
          accessibilityRole="button"
          accessibilityLabel={Strings.chatSendBtn}
        >
          {loading
            ? <ActivityIndicator size="small" color={Colors.primary} />
            : <Text style={[
                chatStyles.sendBtnText,
                (input.trim().length === 0) && chatStyles.sendBtnTextDisabled,
              ]}>↑</Text>
          }
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

// ── Local styles ───────────────────────────────────────────────────────────────

const localStyles = StyleSheet.create({
  charCount: {
    fontSize:    FontSize.xs,
    color:       Colors.textMuted,
    textAlign:   'right',
    paddingRight: Spacing.xs,
    paddingBottom: 2,
  },
  charCountWarn: {
    color: Colors.warning,
  },
  clearBtn: {
    paddingHorizontal: Spacing.sm,
    paddingVertical:   Spacing.xs,
    borderRadius:      Radius.sm,
  },
  clearBtnPressed: {
    backgroundColor: 'rgba(255,255,255,0.15)',
  },
  clearBtnText: {
    fontSize:   FontSize.sm,
    color:      Colors.white,
    fontWeight: FontWeight.medium,
  },
});
