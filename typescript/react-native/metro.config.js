const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const defaultConfig = getDefaultConfig(__dirname);

// Create aliases for Node.js modules to their React Native alternatives
defaultConfig.resolver.extraNodeModules = {
  // File system and OS modules
  os: require.resolve('react-native-os'),
  fs: require.resolve('react-native-fs'),
  path: require.resolve('react-native-path'),
  
  // Crypto module
  crypto: require.resolve('crypto-js'),
  
  // Stream module
  stream: require.resolve('stream-browserify'),
  
  // HTTP modules - use browserify versions
  'node:http': require.resolve('http-browserify'),
  'node:https': require.resolve('https-browserify'),
  http: require.resolve('http-browserify'),
  https: require.resolve('https-browserify'),
  
  // Additional Node.js modules
  events: require.resolve('events'),
  inherits: require.resolve('inherits'),
  url: require.resolve('url'),
  util: require.resolve('util'),
  buffer: require.resolve('buffer'),
  process: require.resolve('process'),
  querystring: require.resolve('querystring'),
  punycode: require.resolve('punycode'),
  assert: require.resolve('assert'),
  constants: require.resolve('constants'),
};

// Ensure React Native platform resolution
defaultConfig.resolver.platforms = ['native', 'react-native', 'ios', 'android', 'web'];

module.exports = defaultConfig;