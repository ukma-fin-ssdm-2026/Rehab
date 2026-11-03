import { Slot } from 'expo-router';

// Keeps legacy placeholder pages inside the authenticated route group.
export default function PlaceholderLayout() {
  return <Slot />;
}
