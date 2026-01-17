import { Tabs } from 'expo-router';
import React from 'react';
import { TouchableOpacity, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { DrawerActions } from '@react-navigation/native';
import { useNavigation } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';

import { HapticTab } from '@/components/haptic-tab';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

const CustomDrawerButton = () => {
  const navigation = useNavigation();

  const openDrawer = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    navigation.dispatch(DrawerActions.openDrawer());
  };

  return (
    <TouchableOpacity
      style={{ padding: 8, marginLeft: 8 }}
      onPress={openDrawer}
    >
      <MaterialCommunityIcons name="menu" size={24} color="#f9f9f9" />
    </TouchableOpacity>
  );
};

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <Tabs
      screenOptions={{
      tabBarActiveTintColor: Colors[colorScheme ?? 'light'].tint,
      headerShown: true,
      headerTransparent: true,
      headerLeft: () => <CustomDrawerButton />,
      headerStyle: {
        backgroundColor: '#15193a',
      },
      tabBarStyle: {
        backgroundColor: '#15193a',
      },
      tabBarButton: HapticTab,
      }}>
      <Tabs.Screen
      name="stackhome"  
      options={{
        title: '',
        tabBarIcon: ({ color }) => <IconSymbol size={28} name="house.fill" color={color} />,
      }}
      />
    </Tabs>
  );
}
