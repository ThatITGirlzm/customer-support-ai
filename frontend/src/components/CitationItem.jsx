/**
 * CitationItem
 *
 * Renders one source citation from a backend ProcessResponse.
 * Tapping the title opens the source URL in the device browser.
 *
 * Props:
 *   citation {object} - A Citation object from the backend response.
 *     citation.passage_id      {string}
 *     citation.source_title    {string}
 *     citation.source_url      {string}
 *     citation.publication_date {string|null}
 *     citation.accessed_date   {string}
 *     citation.section_or_page {string}
 */

import React, { useCallback } from 'react';
import { View, Text, Linking, Pressable } from 'react-native';

import responseCardStyles from '../styles/responseCardStyles';

export default function CitationItem({ citation }) {
  const {
    source_title,
    source_url,
    publication_date,
    accessed_date,
    section_or_page,
  } = citation;

  const handlePress = useCallback(() => {
    if (source_url) {
      Linking.openURL(source_url).catch(() => {
        // Silently ignore — the URL may not be reachable in demo mode.
      });
    }
  }, [source_url]);

  // Build a compact meta string: "Published Mar 2026 · Accessed 2026-11-11"
  const metaParts = [];
  if (publication_date) metaParts.push(`Published ${publication_date}`);
  if (accessed_date)    metaParts.push(`Accessed ${accessed_date}`);
  const metaLine = metaParts.join(' · ');

  return (
    <View style={responseCardStyles.citationItem}>
      {/* Bullet */}
      <View style={responseCardStyles.citationBullet} />

      {/* Content */}
      <View style={responseCardStyles.citationBody}>
        <Pressable onPress={handlePress} accessibilityRole="link">
          <Text style={responseCardStyles.citationTitle} numberOfLines={2}>
            {source_title}
          </Text>
        </Pressable>

        {metaLine ? (
          <Text style={responseCardStyles.citationMeta}>{metaLine}</Text>
        ) : null}

        {section_or_page ? (
          <Text style={responseCardStyles.citationSection}>{section_or_page}</Text>
        ) : null}
      </View>
    </View>
  );
}
