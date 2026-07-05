import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0d1117",
        surface: "#161b22",
        border: "#21262d",
        muted: "#6e7681",
        green: "#3fb950",
        red: "#f85149",
        blue: "#58a6ff",
        orange: "#e3b341",
        purple: "#bc8cff",
      },
    },
  },
  plugins: [],
};
export default config;
