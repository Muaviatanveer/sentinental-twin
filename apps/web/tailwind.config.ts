import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                canvas: "#FAFAFA",
                surface: "#FFFFFF",
                ink: "#171717",
                muted: "#525252",
                border: "#E5E5E5",
            },
        },
    },
    plugins: [],
};

export default config;