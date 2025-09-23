import React from 'react';
import { isComponentEnabled, CONFIG } from '../config/appConfig';

interface ConditionalProps {
  condition: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const ConditionalWrapper: React.FC<ConditionalProps> = ({
  condition,
  children,
  fallback = null
}) => {
  const isEnabled = isComponentEnabled(condition);

  if (process.env.NODE_ENV === 'development' && !isEnabled) {
    // Use a proper template literal so the string is terminated correctly
    console.log(`Component hidden by config (${CONFIG.preset}): ${condition}`);
  }

  return isEnabled ? <>{children}</> : <>{fallback}</>;
};

// Simple hook for configuration
export const useConfig = () => ({
  config: CONFIG,
  isComponentEnabled,
});
