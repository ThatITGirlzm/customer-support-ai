/**
 * Design token: typography scale for the Averse app.
 *
 * Sizes follow a Major Third (1.25×) modular scale.
 * Line heights are set for comfortable reading on mobile.
 * Font families degrade gracefully to system defaults.
 */

const FontFamily = {
  regular:  'System',   // platform default sans-serif
  medium:   'System',
  semiBold: 'System',
  bold:     'System',
  mono:     'monospace', // for request IDs, codes
};

const FontSize = {
  xs:   11,
  sm:   13,
  base: 15,
  md:   17,
  lg:   20,
  xl:   24,
  xxl:  30,
};

const FontWeight = {
  regular:  '400',
  medium:   '500',
  semiBold: '600',
  bold:     '700',
};

const LineHeight = {
  tight:   1.2,   // headings
  normal:  1.5,   // body text
  relaxed: 1.75,  // long-form passages
};

/** Pre-composed text style presets — use these in StyleSheet objects */
const TextStyles = {
  h1: {
    fontSize:   FontSize.xxl,
    fontWeight: FontWeight.bold,
    lineHeight: FontSize.xxl * LineHeight.tight,
  },
  h2: {
    fontSize:   FontSize.xl,
    fontWeight: FontWeight.bold,
    lineHeight: FontSize.xl * LineHeight.tight,
  },
  h3: {
    fontSize:   FontSize.lg,
    fontWeight: FontWeight.semiBold,
    lineHeight: FontSize.lg * LineHeight.tight,
  },
  bodyLarge: {
    fontSize:   FontSize.md,
    fontWeight: FontWeight.regular,
    lineHeight: FontSize.md * LineHeight.normal,
  },
  body: {
    fontSize:   FontSize.base,
    fontWeight: FontWeight.regular,
    lineHeight: FontSize.base * LineHeight.normal,
  },
  bodySmall: {
    fontSize:   FontSize.sm,
    fontWeight: FontWeight.regular,
    lineHeight: FontSize.sm * LineHeight.normal,
  },
  caption: {
    fontSize:   FontSize.xs,
    fontWeight: FontWeight.regular,
    lineHeight: FontSize.xs * LineHeight.normal,
  },
  label: {
    fontSize:   FontSize.sm,
    fontWeight: FontWeight.semiBold,
    lineHeight: FontSize.sm * LineHeight.tight,
  },
  mono: {
    fontFamily: FontFamily.mono,
    fontSize:   FontSize.xs,
    lineHeight: FontSize.xs * LineHeight.normal,
  },
};

export { FontFamily, FontSize, FontWeight, LineHeight, TextStyles };
