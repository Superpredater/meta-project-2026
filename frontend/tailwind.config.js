/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        bg:       '#0f1117',
        surface:  '#1a1d27',
        surface2: '#22263a',
        surface3: '#2a2f47',
        border:   '#2e3350',
        accent:   '#6c63ff',
        accent2:  '#a78bfa',
        'accent-hover': '#5a52e0',
      },
      boxShadow: {
        'glow-accent': '0 0 20px rgba(108, 99, 255, 0.15)',
        'glow-green':  '0 0 12px rgba(34, 197, 94, 0.2)',
        'card': '0 4px 24px rgba(0, 0, 0, 0.4)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
        'pulse-dot': 'pulseDot 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        pulseDot: { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0.4' } },
      },
    },
  },
  plugins: [],
}
