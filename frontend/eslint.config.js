import js from '@eslint/js'
import vue from 'eslint-plugin-vue'

export default [
  js.configs.recommended,
  ...vue.configs['flat/recommended'],
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        browser: true,
      },
    },
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/html-self-closing': 'off',
    },
  },
  {
    ignores: ['dist/', 'node_modules/'],
  },
]
