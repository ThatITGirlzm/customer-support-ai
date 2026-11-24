/**
 * App.js — root entry point for the Averse React Native app.
 *
 * Responsibilities:
 *   1. Wrap the app in SafeAreaProvider (required by react-native-safe-area-context).
 *   2. Wrap the app in NavigationContainer (required by React Navigation).
 *   3. Mount AppNavigator, which owns the full screen stack.
 *
 * Nothing else lives here. All screen logic, styles, and state belong in
 * src/screens/, src/components/, etc.
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider }    from 'react-native-safe-area-context';

import AppNavigator from './src/navigation/AppNavigator';

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <AppNavigator />
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
