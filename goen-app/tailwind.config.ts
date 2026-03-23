import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cosmos: {
          bg: "#0a0a1a",
          surface: "#12122a",
          accent: "#6366f1",
          star: "#f0f0ff",
          dim: "#4a4a6a",
          warm: "#f59e0b",
          glow: "#818cf8",
        },
      },
      fontFamily: {
        sans: ['"Noto Sans JP"', "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
