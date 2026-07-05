import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        "on-error-container": "#ffdad6",
        "on-tertiary": "#003824",
        "on-surface-variant": "#c7c4d7",
        "secondary-fixed": "#c9e6ff",
        "surface-container": "#201f20",
        "surface-container-highest": "#353436",
        "on-primary": "#1000a9",
        "inverse-primary": "#494bd6",
        "tertiary": "#4edea3",
        "secondary": "#89ceff",
        "on-tertiary-fixed": "#002113",
        "on-secondary-container": "#00344e",
        "surface-container-lowest": "#0e0e0f",
        "on-tertiary-container": "#000703",
        "tertiary-fixed": "#6ffbbe",
        "surface": "#131314",
        "on-primary-fixed-variant": "#2f2ebe",
        "inverse-surface": "#e5e2e3",
        "surface-container-high": "#2a2a2b",
        "outline-variant": "#464554",
        "primary-fixed": "#e1e0ff",
        "secondary-container": "#00a2e6",
        "on-error": "#690005",
        "tertiary-fixed-dim": "#4edea3",
        "surface-variant": "#353436",
        "error": "#ffb4ab",
        "on-secondary-fixed": "#001e2f",
        "primary-container": "#8083ff",
        "surface-container-low": "#1c1b1c",
        "outline": "#908fa0",
        "on-surface": "#e5e2e3",
        "surface-tint": "#c0c1ff",
        "surface-dim": "#131314",
        "on-secondary-fixed-variant": "#004c6e",
        "tertiary-container": "#00885d",
        "on-secondary": "#00344d",
        "primary": "#c0c1ff",
        "error-container": "#93000a",
        "primary-fixed-dim": "#c0c1ff",
        "on-tertiary-fixed-variant": "#005236",
        "on-primary-container": "#0d0096",
        "secondary-fixed-dim": "#89ceff",
        "on-primary-fixed": "#07006c",
        "surface-bright": "#3a393a",
        "background": "#050505",
        "on-background": "#e5e2e3",
        "inverse-on-surface": "#313031"
      },
      borderRadius: {
        "DEFAULT": "0.125rem",
        "lg": "0.25rem",
        "xl": "0.5rem",
        "full": "0.75rem"
      },
      spacing: {
        "xl": "40px",
        "gutter": "20px",
        "container-max": "1440px",
        "base": "4px",
        "sm": "8px",
        "md": "16px",
        "lg": "24px",
        "xs": "4px"
      },
      fontFamily: {
        "body-sm": ["Inter", "sans-serif"],
        "label-caps": ["Geist", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "headline-sm": ["Hanken Grotesk", "sans-serif"],
        "headline-md": ["Hanken Grotesk", "sans-serif"],
        "display-lg": ["Hanken Grotesk", "sans-serif"],
        "mono-data": ["Geist", "monospace"]
      },
      fontSize: {
        "body-sm": ["13px", {"lineHeight": "1.5", "fontWeight": "400"}],
        "label-caps": ["11px", {"lineHeight": "1", "letterSpacing": "0.05em", "fontWeight": "600"}],
        "body-md": ["14px", {"lineHeight": "1.6", "fontWeight": "400"}],
        "headline-sm": ["18px", {"lineHeight": "1.4", "fontWeight": "600"}],
        "headline-md": ["24px", {"lineHeight": "1.3", "letterSpacing": "-0.01em", "fontWeight": "600"}],
        "display-lg": ["48px", {"lineHeight": "1.1", "letterSpacing": "-0.02em", "fontWeight": "700"}],
        "mono-data": ["13px", {"lineHeight": "1", "letterSpacing": "-0.01em", "fontWeight": "400"}]
      }
    },
  },
  plugins: [],
};

export default config;
