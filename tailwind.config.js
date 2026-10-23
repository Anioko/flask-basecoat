/** @type {import('tailwindcss').Config} */
function withOpacity(variableName) {
  return ({ opacityValue }) => {
    if (opacityValue !== undefined) {
      return `color-mix(in srgb, var(${variableName}) calc(100% * ${opacityValue}), transparent)`;
    }
    return `var(${variableName})`;
  };
}

module.exports = {
  darkMode: ["class"],
  content: [
    "./app/templates/**/*.html",
    "./app/static/scripts/**/*.js",
    "./flask_basecoat/templates/**/*.html",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif'
        ],
      },
      colors: {
        border: withOpacity('--border'),
        input: withOpacity('--input'),
        ring: withOpacity('--ring'),
        background: withOpacity('--background'),
        foreground: withOpacity('--foreground'),
        primary: {
          DEFAULT: withOpacity('--primary'),
          foreground: withOpacity('--primary-foreground'),
        },
        secondary: {
          DEFAULT: withOpacity('--secondary'),
          foreground: withOpacity('--secondary-foreground'),
        },
        destructive: {
          DEFAULT: withOpacity('--destructive'),
          foreground: withOpacity('--destructive-foreground'),
        },
        muted: {
          DEFAULT: withOpacity('--muted'),
          foreground: withOpacity('--muted-foreground'),
        },
        accent: {
          DEFAULT: withOpacity('--accent'),
          foreground: withOpacity('--accent-foreground'),
        },
        popover: {
          DEFAULT: withOpacity('--popover'),
          foreground: withOpacity('--popover-foreground'),
        },
        card: {
          DEFAULT: withOpacity('--card'),
          foreground: withOpacity('--card-foreground'),
        },
        sidebar: {
          DEFAULT: withOpacity('--sidebar'),
          foreground: withOpacity('--sidebar-foreground'),
          primary: withOpacity('--sidebar-primary'),
          "primary-foreground": withOpacity('--sidebar-primary-foreground'),
          accent: withOpacity('--sidebar-accent'),
          "accent-foreground": withOpacity('--sidebar-accent-foreground'),
          border: withOpacity('--sidebar-border'),
          ring: withOpacity('--sidebar-ring'),
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
