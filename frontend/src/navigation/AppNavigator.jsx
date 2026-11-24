/**
 * AppNavigator
 *
 * Defines the full navigation tree for the Averse app using
 * React Navigation's native stack navigator.
 *
 * Screen registry:
 *   Home   — landing screen (no header chrome from React Navigation;
 *             our own Header component handles it)
 *   Chat   — conversation screen
 *   About  — app info and health check
 *
 * All React Navigation built-in headers are hidden (headerShown: false)
 * because every screen manages its own Header component. This keeps header
 * styling fully under our control and avoids double-header issues.
 *
 * The NavigationContainer is NOT included here — it lives in App.js so the
 * container lifecycle stays at the root level and is easy to wrap with
 * providers (theme, auth, etc.) in future.
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import HomeScreen  from '../screens/HomeScreen';
import ChatScreen  from '../screens/ChatScreen';
import AboutScreen from '../screens/AboutScreen';

const Stack = createNativeStackNavigator();

/** Shared screen options applied to every screen in the stack. */
const SCREEN_OPTIONS = {
  headerShown:   false,   // we use our own Header component
  animation:     'slide_from_right',
  gestureEnabled: true,
};

export default function AppNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="Home"
      screenOptions={SCREEN_OPTIONS}
    >
      <Stack.Screen
        name="Home"
        component={HomeScreen}
        options={{ animation: 'fade' }}   // softer entry for the root screen
      />

      <Stack.Screen
        name="Chat"
        component={ChatScreen}
        // initialParams so ChatScreen never crashes if params are absent
        initialParams={{ initialQuestion: '' }}
      />

      <Stack.Screen
        name="About"
        component={AboutScreen}
      />
    </Stack.Navigator>
  );
}
