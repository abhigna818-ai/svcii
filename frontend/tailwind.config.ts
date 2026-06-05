import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        ink:         '#0D0D0D',
        paper:       '#F5F2EB',
        'paper-2':   '#EDE9DF',
        'paper-3':   '#E2DDD2',
        accent:      '#1B4332',
        'accent-2':  '#2D6A4F',
        'signal-red':'#C1121F',
        'signal-amb':'#E76F00',
        'signal-grn':'#386641',
        muted:       '#6B6560',
      },
      fontFamily: {
        display: ['Playfair Display', 'Georgia', 'serif'],
        body:    ['IBM Plex Sans', 'system-ui', 'sans-serif'],
        mono:    ['IBM Plex Mono', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
