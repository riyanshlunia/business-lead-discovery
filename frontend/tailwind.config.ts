import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          50: '#f8fafc',
          100: '#eef2ff',
          900: '#0f172a',
        },
        accent: {
          500: '#0f766e',
          600: '#115e59',
        },
      },
      boxShadow: {
        glow: '0 20px 80px rgba(15, 118, 110, 0.18)',
      },
      backgroundImage: {
        'hero-grid': 'radial-gradient(circle at top, rgba(15,118,110,0.24), transparent 36%), linear-gradient(180deg, rgba(15,23,42,0.98), rgba(15,23,42,0.92))',
      },
    },
  },
  plugins: [],
};

export default config;
