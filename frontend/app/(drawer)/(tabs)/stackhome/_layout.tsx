import { Stack } from 'expo-router';
import React from 'react';

export default function StackLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: '' }} />
      <Stack.Screen name="results" options={{ title: 'Results' }} />
    </Stack>
  );
}
