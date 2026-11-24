/**
 * Design token: spacing scale for the Averse app.
 *
 * Uses an 8-point base grid. All padding, margin, gap, and
 * border-radius values in the app should reference this file.
 */

const Spacing = {
  xxs:  2,
  xs:   4,
  sm:   8,
  md:   16,
  lg:   24,
  xl:   32,
  xxl:  48,
  xxxl: 64,
};

/** Border radius presets */
const Radius = {
  xs:   4,
  sm:   8,
  md:   12,
  lg:   16,
  xl:   24,
  pill: 999,  // fully rounded (buttons, badges)
};

/** Elevation / shadow presets (used with shadow* props on iOS, elevation on Android) */
const Shadow = {
  none: {},
  sm: {
    shadowColor:   '#000',
    shadowOffset:  { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius:  3,
    elevation:     2,
  },
  md: {
    shadowColor:   '#000',
    shadowOffset:  { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius:  6,
    elevation:     4,
  },
  lg: {
    shadowColor:   '#000',
    shadowOffset:  { width: 0, height: 4 },
    shadowOpacity: 0.16,
    shadowRadius:  12,
    elevation:     8,
  },
};

export { Spacing, Radius, Shadow };
