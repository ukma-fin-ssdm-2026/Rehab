import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { View, StyleSheet } from 'react-native';
import type { ComponentProps } from 'react';

import { Tabs } from 'expo-router';
import { theme } from '../../constants/theme';
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
  const insets = useSafeAreaInsets();
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#DFB5FF',
        tabBarInactiveTintColor: theme.colors.muted,
        tabBarLabelStyle: { fontSize: 10, fontWeight: '400' },
        tabBarIconStyle: { height: 36 },
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border, borderColor: theme.colors.border,
          borderWidth: 1, borderRadius: 28, height: 78 + insets.bottom,
          paddingTop: 8, paddingBottom: 8 + insets.bottom, marginHorizontal: 10, marginBottom: 8,
          ...theme.effects.card,
        },
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: 'Головна',
          tabBarIcon: ({ color, size, focused }) => (
            <NavIcon focused={focused} name="home-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="calendar"
        options={{
          title: 'Календар',
          tabBarIcon: ({ color, size, focused }) => (
            <NavIcon focused={focused} name="calendar-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="goals"
        options={{
          title: 'Цілі',
          tabBarIcon: ({ color, size, focused }) => (
            <NavIcon focused={focused} name="flag-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="statistics"
        options={{
          title: 'Статистика',
          tabBarIcon: ({ color, size, focused }) => (
            <NavIcon focused={focused} name="stats-chart-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Профіль',
          tabBarIcon: ({ color, size, focused }) => (
            <NavIcon focused={focused} name="person-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="friends-support"
        options={{
          title: 'Підтримка',
          tabBarIcon: ({ color, size, focused }) => (
            <NavIcon focused={focused} name="people-outline" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}

function NavIcon({name, size, color, focused}: ComponentProps<typeof Ionicons> & {focused:boolean}) {
  return <View style={[navStyles.icon, focused && navStyles.active]}>
    <Ionicons name={name} size={size} color={color} />
  </View>;
}
const navStyles=StyleSheet.create({
  icon:{width:38,height:36,borderRadius:14,alignItems:'center',justifyContent:'center',borderWidth:1,borderColor:'transparent'},
  active:{backgroundColor:'#3B2949',borderColor:'#765389',boxShadow:'inset 0 1px 0 rgba(244,214,255,0.25), 0 0 14px rgba(178,117,223,0.28)'},
});
