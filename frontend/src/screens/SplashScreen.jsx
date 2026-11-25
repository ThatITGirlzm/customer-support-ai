/**
 * SplashScreen - Animated welcome screen
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  Animated,
  Pressable,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import Colors from '../constants/colors';
import { FontSize, FontWeight } from '../constants/typography';
import { Spacing } from '../constants/spacing';

const { width, height } = Dimensions.get('window');

export default function SplashScreen({ navigation }) {
  const logoScale = useRef(new Animated.Value(0)).current;
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const taglineOpacity = useRef(new Animated.Value(0)).current;
  const shaderRotate = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(logoScale, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
      Animated.timing(logoOpacity, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();

    setTimeout(() => {
      Animated.timing(taglineOpacity, {
        toValue: 1,
        duration: 1200,
        useNativeDriver: true,
      }).start();
    }, 800);

    Animated.loop(
      Animated.timing(shaderRotate, {
        toValue: 1,
        duration: 20000,
        useNativeDriver: true,
      })
    ).start();

    const timer = setTimeout(() => {
      navigation.replace('Home');
    }, 15000);

    return () => clearTimeout(timer);
  }, [navigation, logoScale, logoOpacity, taglineOpacity, shaderRotate]);

  const rotateInterpolate = shaderRotate.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <Pressable 
      style={styles.container} 
      onPress={() => navigation.replace('Home')}
    >
      <Animated.View
        style={[
          styles.shaderLayer,
          { transform: [{ rotate: rotateInterpolate }] },
        ]}
      >
        <LinearGradient
          colors={[Colors.primary, Colors.primaryLight, Colors.primary, Colors.primaryDark]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.gradient}
        />
      </Animated.View>

      <View style={styles.content}>
        <Animated.View
          style={[
            styles.logoContainer,
            {
              opacity: logoOpacity,
              transform: [{ scale: logoScale }],
            },
          ]}
        >
          <View style={styles.logoBox}>
            <Text style={styles.logoText}>A</Text>
          </View>
          <Text style={styles.brandName}>Averse</Text>
        </Animated.View>

        <Animated.Text style={[styles.tagline, { opacity: taglineOpacity }]}>
          Your trusted AI Banking Assistant
        </Animated.Text>

        <Animated.Text style={[styles.skipHint, { opacity: taglineOpacity }]}>
          Tap anywhere to continue
        </Animated.Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.primary,
  },
  shaderLayer: {
    position: 'absolute',
    width: width * 2,
    height: height * 2,
    left: -width / 2,
    top: -height / 2,
    opacity: 0.3,
  },
  gradient: {
    flex: 1,
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.xl,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: Spacing.xxl,
  },
  logoBox: {
    width: 120,
    height: 120,
    borderRadius: 30,
    backgroundColor: Colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 12,
  },
  logoText: {
    fontSize: 72,
    fontWeight: FontWeight.bold,
    color: Colors.primary,
    letterSpacing: -2,
  },
  brandName: {
    fontSize: 56,
    fontWeight: FontWeight.bold,
    color: Colors.white,
    letterSpacing: 2,
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 8,
  },
  tagline: {
    fontSize: FontSize.lg,
    fontWeight: FontWeight.medium,
    color: Colors.white,
    textAlign: 'center',
    letterSpacing: 0.5,
    lineHeight: FontSize.lg * 1.5,
    textShadowColor: 'rgba(0,0,0,0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  skipHint: {
    position: 'absolute',
    bottom: Spacing.xxl,
    fontSize: FontSize.sm,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
  },
});
