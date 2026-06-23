import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'bg-base':     '#0a0f0a',
        'bg-surface':  '#0f1a0f',
        'bg-elevated': '#152115',
        border:        '#1e2e1e',
        'green-primary': '#22c55e',
        'green-dim':     '#16a34a',
        'green-glow':    '#4ade80',
        yellow: '#eab308',
        orange: '#f97316',
        red:    '#ef4444',
        'text-primary':   '#f0fdf0',
        'text-secondary': '#86efac',
        'text-muted':     '#4b7a4b',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'Courier New', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '2px',
      },
    },
  },
  plugins: [],
};

export default config;
