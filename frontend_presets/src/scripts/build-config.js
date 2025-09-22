// scripts/build-config.js
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

class BuildConfigManager {
  constructor() {
    this.configPath = path.join(__dirname, '../frontend/src/config');
    this.presetsPath = path.join(this.configPath, 'presets.yaml');
    this.configFile = path.join(this.configPath, 'config.yaml');
    this.outputPath = path.join(__dirname, '../frontend/src/generated');
  }

  loadConfig() {
    try {
      // Read the main config file
      const configContent = fs.readFileSync(this.configFile, 'utf8');
      const config = yaml.load(configContent);

      // If a preset is specified, load that preset
      if (config.preset && config.preset !== 'custom') {
        return this.loadPreset(config.preset);
      }

      return config;
    } catch (error) {
      console.error('❌ Failed to load configuration:', error.message);
      console.log('📋 Falling back to basic preset');
      return this.loadPreset('basic');
    }
  }

  loadPreset(presetName) {
    try {
      const presetsContent = fs.readFileSync(this.presetsPath, 'utf8');
      const presets = yaml.loadAll(presetsContent);
      
      // Find the preset by name
      const preset = presets.find(p => p && p.preset === presetName);
      
      if (!preset) {
        console.error(`❌ Preset '${presetName}' not found`);
        console.log('📋 Available presets:', presets.map(p => p?.preset).filter(Boolean));
        process.exit(1);
      }

      return preset;
    } catch (error) {
      console.error('❌ Failed to load presets:', error.message);
      process.exit(1);
    }
  }

  generateTypeDefinitions(config) {
    const typeDefinitions = `
// AUTO-GENERATED FILE - DO NOT EDIT
// Generated from configuration: ${config.preset}

export interface AppConfig {
  preset: string;
  pages: {
    ${Object.entries(config.pages).map(([key, value]) => 
      `${key}: ${value};`
    ).join('\n    ')}
  };
  components: {
    header: {
      ${Object.entries(config.components.header).map(([key, value]) => 
        `${key}: ${value};`
      ).join('\n      ')}
    };
    call_test: {
      ${Object.entries(config.components.call_test).map(([key, value]) => {
        if (typeof value === 'object') {
          return `${key}: {
        ${Object.entries(value).map(([subKey, subValue]) => 
          `${subKey}: ${subValue};`
        ).join('\n        ')}
      };`;
        }
        return `${key}: ${value};`;
      }).join('\n      ')}
    };
    // Add other component types...
  };
}

export const APP_CONFIG: AppConfig = ${JSON.stringify(config, null, 2)} as const;

// Feature flags for conditional compilation
export const FEATURES = {
  CALL_TEST: ${config.pages.call_test},
  CHAT_HISTORY: ${config.pages.chat_history},
  DASHBOARD: ${config.pages.dashboard},
  FEEDBACK: ${config.pages.feedback},
  VOICE_SELECTION: ${config.components.call_test.talk_to_vaani.voice_selection},
  FLOATING_CHAT: ${config.components.global.floating_chat_widget},
  // Add more feature flags as needed
} as const;
`;

    return typeDefinitions;
  }

  generateRoutesConfig(config) {
    const enabledRoutes = [];
    
    if (config.pages.signin) {
      enabledRoutes.push(`{ path: "/sign-in", component: "SignIn", protected: false }`);
    }
    
    if (config.pages.call_test) {
      enabledRoutes.push(`{ path: "/", component: "Home", protected: true }`);
      enabledRoutes.push(`{ path: "/home", component: "Home", protected: true }`);
    }
    
    if (config.pages.dashboard) {
      enabledRoutes.push(`{ path: "/dashboard", component: "Dashboard", protected: true }`);
    }
    
    if (config.pages.call_history) {
      enabledRoutes.push(`{ path: "/history", component: "History", protected: true }`);
    }
    
    if (config.pages.feedback) {
      enabledRoutes.push(`{ path: "/feedback", component: "Feedback", protected: true }`);
    }

    const routesConfig = `
// AUTO-GENERATED FILE - DO NOT EDIT
// Generated from configuration: ${config.preset}

export const ENABLED_ROUTES = [
  ${enabledRoutes.join(',\n  ')}
] as const;

export const PAGE_PATHS = {
  ${config.pages.signin ? 'signin: "/sign-in",' : ''}
  ${config.pages.call_test ? 'landing: "/", home: "/home",' : ''}
  ${config.pages.dashboard ? 'dashboard: "/dashboard",' : ''}
  ${config.pages.call_history ? 'history: "/history",' : ''}
  ${config.pages.feedback ? 'feedback: "/feedback",' : ''}
} as const;

export const MENU_ITEMS = [
  ${config.components.header.dashboard_menu && config.pages.dashboard ? 
    '{ label: "Dashboard", icon: "pi pi-chart-bar", url: "/dashboard" },' : ''}
  ${config.components.header.call_test_menu && config.pages.call_test ? 
    '{ label: "Call Test", icon: "pi pi-phone", url: "/home" },' : ''}
  ${config.components.header.call_history_menu && config.pages.call_history ? 
    '{ label: "Call History", icon: "pi pi-history", url: "/history" },' : ''}
  ${config.components.header.feedback_menu && config.pages.feedback ? 
    '{ label: "Feedback", icon: "pi pi-comment", url: "/feedback" },' : ''}
].filter(Boolean);
`;

    return routesConfig;
  }

  generateWebpackConfig(config) {
    const webpackConfig = `
// AUTO-GENERATED FILE - DO NOT EDIT
// Generated from configuration: ${config.preset}

const { DefinePlugin } = require('webpack');

const configPlugins = [
  new DefinePlugin({
    '__CONFIG_PRESET__': JSON.stringify('${config.preset}'),
    '__FEATURES__': {
      CALL_TEST: ${config.pages.call_test},
      CHAT_HISTORY: ${config.pages.chat_history},
      DASHBOARD: ${config.pages.dashboard},
      FEEDBACK: ${config.pages.feedback},
      VOICE_SELECTION: ${config.components.call_test.talk_to_vaani.voice_selection},
      FLOATING_CHAT: ${config.components.global.floating_chat_widget},
    }
  })
];

module.exports = { configPlugins };
`;

    return webpackConfig;
  }

  build() {
    console.log('🔧 Starting configuration build process...');
    
    // Load configuration
    const config = this.loadConfig();
    
    console.log(`✅ Loaded configuration: ${config.preset}`);
    
    // Create output directory if it doesn't exist
    if (!fs.existsSync(this.outputPath)) {
      fs.mkdirSync(this.outputPath, { recursive: true });
    }

    // Generate type definitions
    const typeDefinitions = this.generateTypeDefinitions(config);
    fs.writeFileSync(path.join(this.outputPath, 'config.ts'), typeDefinitions);
    console.log('✅ Generated TypeScript definitions');

    // Generate routes configuration
    const routesConfig = this.generateRoutesConfig(config);
    fs.writeFileSync(path.join(this.outputPath, 'routes.ts'), routesConfig);
    console.log('✅ Generated routes configuration');

    // Generate webpack configuration
    const webpackConfig = this.generateWebpackConfig(config);
    fs.writeFileSync(path.join(this.outputPath, 'webpack.config.js'), webpackConfig);
    console.log('✅ Generated webpack configuration');

    // Copy config files for runtime access
    fs.writeFileSync(
      path.join(this.outputPath, 'runtime-config.json'),
      JSON.stringify(config, null, 2)
    );
    console.log('✅ Generated runtime configuration');

    // Validate configuration
    this.validateConfiguration(config);
    
    console.log('🎉 Configuration build completed successfully!');
    console.log(`📋 Current preset: ${config.preset}`);
    console.log(`📄 Enabled pages: ${Object.entries(config.pages)
      .filter(([, enabled]) => enabled)
      .map(([page]) => page)
      .join(', ')}`);
  }

  validateConfiguration(config) {
    const errors = [];
    const warnings = [];

    // Page-menu consistency validation
    if (!config.pages.dashboard && config.components.header.dashboard_menu) {
      errors.push("Dashboard page is disabled but dashboard menu is enabled");
    }
    if (!config.pages.call_test && config.components.header.call_test_menu) {
      errors.push("Call test page is disabled but call test menu is enabled");
    }
    if (!config.pages.call_history && config.components.header.call_history_menu) {
      errors.push("Call history page is disabled but call history menu is enabled");
    }
    if (!config.pages.feedback && config.components.header.feedback_menu) {
      errors.push("Feedback page is disabled but feedback menu is enabled");
    }

    // Component dependencies validation
    if (config.components.call_test.talk_to_vaani.voice_options_dropdown && 
        !config.components.call_test.talk_to_vaani.voice_selection) {
      warnings.push("Voice options dropdown is enabled but voice selection is disabled");
    }

    // Chat widget validation
    if (config.components.global.floating_chat_widget && 
        !config.pages.chat_history) {
      warnings.push("Floating chat widget is enabled but chat history page is disabled");
    }

    // Report validation results
    if (errors.length > 0) {
      console.error('❌ Configuration validation errors:');
      errors.forEach(error => console.error(`  - ${error}`));
      process.exit(1);
    }

    if (warnings.length > 0) {
      console.warn('⚠️  Configuration validation warnings:');
      warnings.forEach(warning => console.warn(`  - ${warning}`));
    }

    if (errors.length === 0 && warnings.length === 0) {
      console.log('✅ Configuration validation passed');
    }
  }

  // Utility methods
  switchPreset(presetName) {
    const presets = ['basic', 'call-only', 'chat-only', 'full'];
    
    if (!presets.includes(presetName)) {
      console.error(`❌ Invalid preset: ${presetName}`);
      console.log(`📋 Available presets: ${presets.join(', ')}`);
      process.exit(1);
    }

    const configContent = `# Frontend Feature Configuration
# Current active preset
preset: "${presetName}"

# This configuration will load the '${presetName}' preset
# To customize, change preset to 'custom' and modify the values below
`;

    fs.writeFileSync(this.configFile, configContent);
    console.log(`✅ Switched to preset: ${presetName}`);
    
    // Rebuild with new preset
    this.build();
  }

  listPresets() {
    try {
      const presetsContent = fs.readFileSync(this.presetsPath, 'utf8');
      const presets = yaml.loadAll(presetsContent);
      
      console.log('📋 Available presets:');
      presets.forEach(preset => {
        if (preset && preset.preset) {
          console.log(`\n🔧 ${preset.preset.toUpperCase()}:`);
          
          // Show enabled pages
          const enabledPages = Object.entries(preset.pages)
            .filter(([, enabled]) => enabled)
            .map(([page]) => page);
          console.log(`  Pages: ${enabledPages.join(', ')}`);
          
          // Show key features
          const keyFeatures = [];
          if (preset.components.call_test.talk_to_vaani.voice_selection) {
            keyFeatures.push('Voice Selection');
          }
          if (preset.components.global.floating_chat_widget) {
            keyFeatures.push('Chat Widget');
          }
          if (preset.components.call_history.csv_download) {
            keyFeatures.push('CSV Download');
          }
          if (preset.components.call_history.call_details_sidebar.conversation_evaluation) {
            keyFeatures.push('Conversation Analysis');
          }
          
          if (keyFeatures.length > 0) {
            console.log(`  Features: ${keyFeatures.join(', ')}`);
          }
        }
      });
    } catch (error) {
      console.error('❌ Failed to list presets:', error.message);
      process.exit(1);
    }
  }
}

// CLI Interface
function main() {
  const manager = new BuildConfigManager();
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case 'build':
      manager.build();
      break;
      
    case 'switch':
      const preset = args[1];
      if (!preset) {
        console.error('❌ Please specify a preset name');
        console.log('Usage: node build-config.js switch <preset-name>');
        process.exit(1);
      }
      manager.switchPreset(preset);
      break;
      
    case 'list':
      manager.listPresets();
      break;
      
    case 'validate':
      const config = manager.loadConfig();
      manager.validateConfiguration(config);
      console.log('✅ Configuration is valid');
      break;
      
    default:
      console.log('🔧 Configuration Build Tool');
      console.log('\nUsage:');
      console.log('  node build-config.js build           # Build configuration files');
      console.log('  node build-config.js switch <preset> # Switch to a preset');
      console.log('  node build-config.js list            # List available presets');
      console.log('  node build-config.js validate        # Validate current config');
      console.log('\nAvailable presets: basic, call-only, chat-only, full');
      break;
  }
}

if (require.main === module) {
  main();
}

module.exports = BuildConfigManager;