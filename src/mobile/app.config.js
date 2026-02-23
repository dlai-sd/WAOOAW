/**
 * Expo App Configuration (Dynamic)
 * 
 * This file generates environment-specific app configuration based on:
 * 1. EAS_BUILD_PROFILE environment variable (set during EAS builds)
 * 2. ENVIRONMENT_OVERRIDE for local development (from .env.local)
 * 
 * Env-specific values:
 * - APP_ENV: current environment (development/demo/uat/prod)
 * - Bundle IDs: com.waooaw.app (production) vs com.waooaw.app.{env} (test)
 * - OAuth redirect scheme: Extracted from client ID
 * 
 * NOTE: This config is applied AFTER EAS reads projectId/owner/slug from app.json,
 * so EAS project properties must remain in app.json for EAS CLI to recognize them.
 */

module.exports = (context = {}) => {
  // Handle both function signature styles
  const config = context.config || {};
  const expoConfig = config.expo || {};
  
  // Determine environment from EAS build profile or override
  const buildProfile = process.env.EAS_BUILD_PROFILE || 'development';
  const environmentOverride = process.env.ENVIRONMENT_OVERRIDE;
  const environment = environmentOverride || buildProfile;

  // Map EAS profile to runtime environment
  const runtimeEnv = {
    development: 'development',
    preview: 'demo',        // Preview profile → demo environment
    demo: 'demo',
    uat: 'uat',
    prod: 'prod',
  }[environment] || 'development';

  // Bundle ID per environment (production uses base ID, others use namespaced)
  const iosBundleId = runtimeEnv === 'development' || runtimeEnv === 'demo'
    ? 'com.waooaw.app'
    : runtimeEnv === 'prod'
    ? 'com.waooaw.app'
    : `com.waooaw.app.${runtimeEnv}`;

  const androidPackage = runtimeEnv === 'development' || runtimeEnv === 'demo'
    ? 'com.waooaw.app'
    : runtimeEnv === 'prod'
    ? 'com.waooaw.app'
    : `com.waooaw.app.${runtimeEnv}`;

  // OAuth redirect scheme based on environment
  // Development: custom scheme for local testing
  // Production (demo/uat/prod): GCP OAuth client-specific scheme
  const oauthRedirectScheme = runtimeEnv === 'development'
    ? 'com.waooaw.dev'
    : 'com.googleusercontent.apps.270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu';

  return {
    ...config,
    expo: {
      ...expoConfig,
      // DO NOT override projectId, owner, or slug - these must stay from app.json for EAS to work
      // Preserve: projectId, owner, slug, and all other base config
      // Runtime environment detection (read by api.config.ts)
      extra: {
        ...(expoConfig.extra || {}),
        APP_ENV: runtimeEnv,
        ENVIRONMENT: runtimeEnv,
        BUILD_PROFILE: environment,
      },
      // iOS configuration
      ios: {
        ...(expoConfig.ios || {}),
        bundleIdentifier: iosBundleId,
      },
      // Android configuration
      android: {
        ...(expoConfig.android || {}),
        package: androidPackage,
        intentFilters: [
          // Universal links
          {
            action: 'VIEW',
            autoVerify: true,
            data: [
              {
                scheme: 'https',
                host: 'waooaw.com',
              },
              {
                scheme: 'waooaw',
              },
            ],
            category: ['BROWSABLE', 'DEFAULT'],
          },
          // OAuth redirect
          {
            action: 'VIEW',
            data: [
              {
                scheme: oauthRedirectScheme,
              },
            ],
            category: ['BROWSABLE', 'DEFAULT'],
          },
        ],
      },
    },
  };
};
