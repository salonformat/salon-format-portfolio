import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  site: 'https://salonformat.github.io',
  base: process.env.NODE_ENV === 'production' ? '/salon-format-portfolio/' : '/',
});
