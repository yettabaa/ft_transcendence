/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#5E4AE3',
                secondary: '#555363',
                third: '#E3BC4B',
                dark: '#2F2E39',
                bg: '#1E1E1E',
                white: '#FFFFFF',
                gray1: '#858585',
                gray2: '#313131',
                gray3: '#1E1E1E',
                black: '#000000'
            },
        },
    },
    plugins: [],
};

