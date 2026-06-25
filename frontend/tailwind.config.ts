import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'bg-base': '#f5f0e8',
        'bg-dark': '#0f1a0e',
        'bg-surface': '#ede8dc',
        'bg-surface-dark': '#162316',
        'green-deep': '#1a3d1a',
        'green-mid': '#2d6a2d',
        'green-bright': '#4a9e4a',
        'green-light': '#a8d5a8',
        'beige-warm': '#c4b99a',
        'beige-light': '#f5f0e8',
        'text-dark': '#1a1a18',
        'text-light': '#f0ede6',
        'text-muted-light': '#6b6355',
        'text-muted-dark': '#7a9e7a',
      },
      fontFamily: {
        serif: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'Courier New', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '4px',
      },
    },
  },
  plugins: [],
};

export default config;
