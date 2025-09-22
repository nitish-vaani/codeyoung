// // frontend/src/components/ConditionalWrapper.tsx
// import React from 'react';
// import configManager from '../config/configManager';

// interface ConditionalWrapperProps {
//   condition: string;
//   children: React.ReactNode;
//   fallback?: React.ReactNode;
// }

// export const ConditionalWrapper: React.FC<ConditionalWrapperProps> = ({ 
//   condition, 
//   children, 
//   fallback = null 
// }) => {
//   const isEnabled = configManager.isComponentEnabled(condition);
//   return isEnabled ? <>{children}</> : <>{fallback}</>;
// };

// // HOC for conditional component rendering
// export function withConditionalRender<T extends object>(
//   WrappedComponent: React.ComponentType<T>,
//   condition: string
// ) {
//   const ConditionalComponent: React.FC<T> = (props) => {
//     const isEnabled = configManager.isComponentEnabled(condition);
    
//     if (!isEnabled) {
//       if (process.env.NODE_ENV === 'development') {
//         console.log(`🚫 Component blocked by config: ${condition}`);
//       }
//       return null;
//     }
    
//     return <WrappedComponent {...props} />;
//   };

//   ConditionalComponent.displayName = `withConditionalRender(${WrappedComponent.displayName || WrappedComponent.name})`;
//   return ConditionalComponent;
// }

// // Hook for checking configuration
// export function useConfig() {
//   return {
//     isPageEnabled: configManager.isPageEnabled.bind(configManager),
//     isComponentEnabled: configManager.isComponentEnabled.bind(configManager),
//     getConfig: configManager.getConfig.bind(configManager),
//     getCurrentPreset: configManager.getCurrentPreset.bind(configManager),
//   };
// }

// // Route configuration generator
// export function generateRoutes() {
//   const config = configManager.getConfig();
//   const routes = [];

//   // Always include signin
//   if (config.pages.signin) {
//     routes.push({
//       path: "/sign-in",
//       component: "SignIn",
//       enabled: true
//     });
//   }

//   if (config.pages.dashboard) {
//     routes.push({
//       path: "/dashboard",
//       component: "Dashboard", 
//       enabled: true
//     });
//   }

//   if (config.pages.call_test) {
//     routes.push(
//       {
//         path: "/",
//         component: "Home",
//         enabled: true
//       },
//       {
//         path: "/home", 
//         component: "Home",
//         enabled: true
//       }
//     );
//   }

//   if (config.pages.call_history) {
//     routes.push({
//       path: "/history",
//       component: "History",
//       enabled: true
//     });
//   }

//   if (config.pages.feedback) {
//     routes.push({
//       path: "/feedback", 
//       component: "Feedback",
//       enabled: true
//     });
//   }

//   return routes.filter(route => route.enabled);
// }

// // Menu items configuration
// export function generateMenuItems() {
//   const config = configManager.getConfig();
//   const menuItems = [];

//   if (config.components.header.dashboard_menu && config.pages.dashboard) {
//     menuItems.push({
//       label: "Dashboard",
//       icon: "pi pi-chart-bar",
//       url: "/dashboard"
//     });
//   }

//   if (config.components.header.call_test_menu && config.pages.call_test) {
//     menuItems.push({
//       label: "Call Test",
//       icon: "pi pi-phone", 
//       url: "/home"
//     });
//   }

//   if (config.components.header.call_history_menu && config.pages.call_history) {
//     menuItems.push({
//       label: "Call History",
//       icon: "pi pi-history",
//       url: "/history"
//     });
//   }

//   if (config.components.header.feedback_menu && config.pages.feedback) {
//     menuItems.push({
//       label: "Feedback", 
//       icon: "pi pi-comment",
//       url: "/feedback"
//     });
//   }

//   return menuItems;
// }

// // Page constants generator
// export function generatePagePaths() {
//   const config = configManager.getConfig();
//   const paths: any = {};

//   if (config.pages.signin) paths.signin = '/sign-in';
//   if (config.pages.dashboard) paths.dashboard = '/dashboard';
//   if (config.pages.call_test) {
//     paths.landing = '/';
//     paths.home = '/home';
//   }
//   if (config.pages.call_history) paths.history = '/history';
//   if (config.pages.feedback) paths.feedback = '/feedback';

//   return paths;
// }

// frontend/src/components/ConditionalWrapper.tsx
// Simple conditional rendering - no external dependencies

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
    console.log(`🚫 Component hidden by config (${CONFIG.preset}):`, condition);
  }
  
  return isEnabled ? <>{children}</> : <>{fallback}</>;
};

// Simple hook for configuration
export const useConfig = () => ({
  config: CONFIG,
  isComponentEnabled,
});