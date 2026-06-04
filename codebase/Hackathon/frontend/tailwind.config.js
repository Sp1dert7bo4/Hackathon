/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        primary: "#2563EB",
        appbg: "#F8FAFC",
        border: "#E5E7EB",
        success: "#10B981",
        warning: "#F59E0B",
      },
      boxShadow: {
        soft: "0 18px 45px rgba(15, 23, 42, 0.10)",
        marker: "0 10px 18px rgba(15, 23, 42, 0.22)",
      },
    },
  },
  plugins: [],
};
