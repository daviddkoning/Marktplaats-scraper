// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  // Enable Nuxt 4 compatibility routing and directory structure
  future: {
    compatibilityVersion: 4,
  },

  // Google AdSense Integration
  app: {
    head: {
      script: [
        {
          src: 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1917329441007803',
          async: true,
          crossorigin: 'anonymous'
        }
      ]
    }
  },

  modules: [
    '@nuxt/eslint',
    '@nuxt/ui'
  ],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://94.237.43.155:8000'
    }
  },

  // Dev only: forward /api requests to FastAPI on the same server
  nitro: {
    devProxy: {
      '/api': {
        target: 'http://127.0.0.1:8000/api',
        changeOrigin: true
      }
    }
  },

  vite: {
    server: {
      allowedHosts: true
    }
  }, // <- this comma was missing

  devtools: {
    enabled: true
  },

  routeRules: {
    '/': { prerender: true }
  },

  compatibilityDate: '2026-06-30',

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})
