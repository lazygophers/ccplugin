/* eslint-disable no-undef */
const path = require('path');

module.exports = {
  // Use the same theme switch mechanism as md2html.js: <html data-theme="dark|light">
  darkMode: ['class', '[data-theme="dark"]'],
  content: [path.join(__dirname, '../../scripts/md2html.py'), path.join(__dirname, './md2html.js')],
  theme: { extend: {} },
  plugins: [],
};
