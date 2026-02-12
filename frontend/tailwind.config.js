/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 简约清新配色方案 - 高级浅色主题
        primary: {
          50: '#f7f7f4',    // 极浅米白
          100: '#f0ece8',   // 浅米色
          200: '#e8e4dc',   // 米色
          300: '#ddd5c7',   // 暖米色
          400: '#d4c4a8',   // 金米色
          500: '#c9a86c',   // 金棕色（主色）
          600: '#b8956f',   // 深金棕
          700: '#8b7355',   // 深棕
          800: '#6b5d4f',   // 深棕灰
          900: '#4a3f38',   // 深棕黑
        },
        accent: {
          50: '#f0f4f3',
          100: '#e0ebe5',
          200: '#c5d9c9',   // 橄榄绿
          300: '#a3c181',   // 深橄榄
          400: '#8da676',    // 橄榄绿
          500: '#7a9658',    // 深橄榄（强调色）
        },
        neutral: {
          50: '#fafafa',   // 极浅灰白
          100: '#f5f5f5',
          200: '#e5e5e5',   // 边框色
          300: '#d4d4d4',
          400: '#a3a3a3',
          500: '#737373',
          600: '#5a5a5a',   // 文字主色
          700: '#3d3d3d',
          800: '#2d2d2d',   // 深色文字
          900: '#1a1a1a',
        }
      },
      fontFamily: {
        display: ['Playfair Display', 'serif'],
        body: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'soft-lg': '0 8px 24px rgba(0, 0, 0, 0.12)',
        'elegant': '0 4px 16px rgba(201, 168, 108, 0.15)',
      },
      animation: {
        'fade-in': 'fade-in 0.4s ease-out',
        'slide-up': 'slide-up 0.5s ease-out',
        'scale-in': 'scale-in 0.3s ease-out',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'scale-in': {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
