/** Nocturnal botanical glass system, shared by every screen. */
export const theme = {
  colors: {
    background: '#0B0A10', surface: '#1B1723', primary: '#624675',
    primaryDark: '#F8F3F8', accent: '#30233D', text: '#F8F3F8',
    muted: '#C4B9C9', border: '#514259', danger: '#F3B1C6',
    dangerSurface: '#38212D', highlight: '#C4D56C', buttonBorder: '#B58BCD',
    hero: '#191422', heroMuted: '#D2C8D7', progressTrack: '#342C3E',
    backdrop: 'rgba(6, 5, 10, 0.84)',
  },
  gradients: {
    card: ['#302637', '#18141F', '#292030'] as const,
    button: ['#79558E', '#593C70', '#705082'] as const,
    outline: ['#292030', '#17131D'] as const,
  },
  effects: {
    card: { boxShadow: 'inset 0 1px 0 rgba(236,203,255,0.22), 0 12px 32px rgba(0,0,0,0.24)' },
    button: { boxShadow: 'inset 0 1px 0 rgba(255,225,255,0.3), 0 5px 22px rgba(155,92,190,0.2)' },
    input: { boxShadow: 'inset 0 2px 9px rgba(0,0,0,0.24)' },
  },
};
