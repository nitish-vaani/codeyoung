// // frontend/src/config/configManager.ts
// import yaml from 'js-yaml';
// import configYaml from './config.yaml?raw';
// import presetsYaml from './presets.yaml?raw';

// // Configuration type definitions
// export interface ConfigSchema {
//   preset: string;
//   pages: {
//     signin: boolean;
//     dashboard: boolean;
//     call_test: boolean;
//     call_history: boolean;
//     chat_history: boolean;
//     feedback: boolean;
//   };
//   components: {
//     header: {
//       dashboard_menu: boolean;
//       call_test_menu: boolean;
//       chat_test_menu: boolean;
//       call_history_menu: boolean;
//       feedback_menu: boolean;
//       user_avatar_dropdown: boolean;
//     };
//     call_test: {
//       tryout_component: boolean;
//       talk_to_vaani_component: boolean;
//       talk_to_vaani: {
//         name_field: boolean;
//         country_code_selector: boolean;
//         phone_number_field: boolean;
//         voice_selection: boolean;
//         voice_options_dropdown: boolean;
//         use_case_dropdown: boolean;
//         trigger_call_button: boolean;
//       };
//     };
//     call_history: {
//       view_mode_toggle: boolean;
//       filters_section: boolean;
//       search_functionality: boolean;
//       date_range_filter: boolean;
//       status_filter: boolean;
//       direction_filter: boolean;
//       selection_checkboxes: boolean;
//       bulk_operations: boolean;
//       csv_download: boolean;
//       call_details_sidebar: {
//         audio_recording: boolean;
//         transcript_section: boolean;
//         summary_section: boolean;
//         conversation_evaluation: boolean;
//         entity_extraction: boolean;
//       };
//     };
//     chat_history: {
//       filters_section: boolean;
//       search_functionality: boolean;
//       date_range_filter: boolean;
//       selection_checkboxes: boolean;
//       csv_download: boolean;
//       chat_details_sidebar: {
//         chat_info_section: boolean;
//         transcript_section: boolean;
//         summary_section: boolean;
//       };
//     };
//     dashboard: {
//       call_metrics: boolean;
//       chat_metrics: boolean;
//       period_toggle: boolean;
//       metrics_cards: boolean;
//       call_trends_chart: boolean;
//       chat_trends_chart: boolean;
//       duration_chart: boolean;
//     };
//     feedback: {
//       rating_sliders: boolean;
//       feedback_text_area: boolean;
//       submit_button: boolean;
//     };
//     global: {
//       floating_chat_widget: boolean;
//       footer: boolean;
//     };
//   };
//   api: {
//     call_endpoints: boolean;
//     chat_endpoints: boolean;
//     dashboard_endpoints: boolean;
//     feedback_endpoints: boolean;
//   };
//   build: {
//     tree_shake_disabled_features: boolean;
//     remove_unused_routes: boolean;
//     conditional_imports: boolean;
//   };
// }

// export interface PresetConfigs {
//   basic: ConfigSchema;
//   'call-only': ConfigSchema;
//   'chat-only': ConfigSchema;
//   full: ConfigSchema;
// }

// class ConfigManager {
//   private config: ConfigSchema;
//   private presets: PresetConfigs;

//   constructor() {
//     try {
//       // Load presets
//       const presetsData = yaml.load(presetsYaml) as any;
//       this.presets = {
//         basic: presetsData.basic,
//         'call-only': presetsData['call-only'],
//         'chat-only': presetsData['chat-only'],
//         full: presetsData.full,
//       };

//       // Load main config
//       const configData = yaml.load(configYaml) as ConfigSchema;
      
//       // If config specifies a preset, load that preset
//       if (configData.preset && configData.preset !== 'custom') {
//         this.config = this.getPresetConfig(configData.preset);
//       } else {
//         this.config = configData;
//       }

//       // Validate the configuration
//       this.validateConfig();
      
//       console.log(`✅ Configuration loaded successfully with preset: ${this.config.preset}`);
//     } catch (error) {
//       console.error('❌ Failed to load configuration:', error);
//       // Fallback to basic preset
//       this.config = this.presets.basic;
//     }
//   }

//   private getPresetConfig(presetName: string): ConfigSchema {
//     const preset = this.presets[presetName as keyof PresetConfigs];
//     if (!preset) {
//       console.warn(`⚠️  Preset '${presetName}' not found, falling back to 'basic'`);
//       return this.presets.basic;
//     }
//     return preset;
//   }

//   private validateConfig(): void {
//     const errors: string[] = [];
//     const warnings: string[] = [];

//     // Validation Rule 1: If a page is disabled, its menu should also be disabled
//     if (!this.config.pages.dashboard && this.config.components.header.dashboard_menu) {
//       errors.push("Dashboard page is disabled but dashboard menu is enabled");
//     }
//     if (!this.config.pages.call_test && this.config.components.header.call_test_menu) {
//       errors.push("Call test page is disabled but call test menu is enabled");
//     }
//     if (!this.config.pages.call_history && this.config.components.header.call_history_menu) {
//       errors.push("Call history page is disabled but call history menu is enabled");
//     }
//     if (!this.config.pages.feedback && this.config.components.header.feedback_menu) {
//       errors.push("Feedback page is disabled but feedback menu is enabled");
//     }

//     // Validation Rule 2: If call_test page is disabled, all its components should be disabled
//     if (!this.config.pages.call_test) {
//       if (this.config.components.call_test.tryout_component) {
//         errors.push("Call test page is disabled but tryout component is enabled");
//       }
//       if (this.config.components.call_test.talk_to_vaani_component) {
//         errors.push("Call test page is disabled but talk to vaani component is enabled");
//       }
//     }

//     // Validation Rule 3: If talk_to_vaani_component is disabled, all its sub-components should be disabled
//     if (!this.config.components.call_test.talk_to_vaani_component) {
//       const talkToVaaniConfig = this.config.components.call_test.talk_to_vaani;
//       Object.entries(talkToVaaniConfig).forEach(([key, value]) => {
//         if (value) {
//           errors.push(`Talk to Vaani component is disabled but ${key} is enabled`);
//         }
//       });
//     }

//     // Validation Rule 4: Voice selection dependencies
//     if (this.config.components.call_test.talk_to_vaani.voice_options_dropdown && 
//         !this.config.components.call_test.talk_to_vaani.voice_selection) {
//       warnings.push("Voice options dropdown is enabled but voice selection is disabled");
//     }

//     // Validation Rule 5: Dashboard metrics validation
//     if (this.config.pages.dashboard) {
//       if (!this.config.components.dashboard.call_metrics && 
//           !this.config.components.dashboard.chat_metrics) {
//         warnings.push("Dashboard page is enabled but no metrics are enabled");
//       }
      
//       if (this.config.components.dashboard.call_trends_chart && 
//           !this.config.components.dashboard.call_metrics) {
//         warnings.push("Call trends chart is enabled but call metrics are disabled");
//       }
      
//       if (this.config.components.dashboard.chat_trends_chart && 
//           !this.config.components.dashboard.chat_metrics) {
//         warnings.push("Chat trends chart is enabled but chat metrics are disabled");
//       }
//     }

//     // Validation Rule 6: History page dependencies
//     if (!this.config.pages.call_history && !this.config.pages.chat_history) {
//       if (this.config.components.call_history.view_mode_toggle) {
//         errors.push("View mode toggle is enabled but no history pages are enabled");
//       }
//     }

//     // Validation Rule 7: API endpoint validation
//     if (this.config.components.global.floating_chat_widget && 
//         !this.config.api.chat_endpoints) {
//       errors.push("Floating chat widget is enabled but chat API endpoints are disabled");
//     }

//     // Validation Rule 8: Floating chat widget validation
//     if (this.config.components.global.floating_chat_widget && 
//         !this.config.pages.chat_history) {
//       warnings.push("Floating chat widget is enabled but chat history page is disabled");
//     }

//     // Report validation results
//     if (errors.length > 0) {
//       console.error('❌ Configuration validation errors:');
//       errors.forEach(error => console.error(`  - ${error}`));
//       throw new Error(`Configuration validation failed with ${errors.length} errors`);
//     }

//     if (warnings.length > 0) {
//       console.warn('⚠️  Configuration validation warnings:');
//       warnings.forEach(warning => console.warn(`  - ${warning}`));
//     }

//     if (errors.length === 0 && warnings.length === 0) {
//       console.log('✅ Configuration validation passed');
//     }
//   }

//   // Public getter methods
//   getConfig(): ConfigSchema {
//     return this.config;
//   }

//   isPageEnabled(page: keyof ConfigSchema['pages']): boolean {
//     return this.config.pages[page];
//   }

//   isComponentEnabled(component: string): boolean {
//     const parts = component.split('.');
//     let current: any = this.config.components;
    
//     for (const part of parts) {
//       if (current[part] === undefined) {
//         return false;
//       }
//       current = current[part];
//     }
    
//     return current === true;
//   }

//   getEnabledPages(): string[] {
//     return Object.entries(this.config.pages)
//       .filter(([, enabled]) => enabled)
//       .map(([page]) => page);
//   }

//   getEnabledMenuItems(): string[] {
//     return Object.entries(this.config.components.header)
//       .filter(([, enabled]) => enabled)
//       .map(([menu]) => menu.replace('_menu', ''));
//   }

//   // Preset management
//   loadPreset(presetName: string): void {
//     this.config = this.getPresetConfig(presetName);
//     this.validateConfig();
//     console.log(`✅ Switched to preset: ${presetName}`);
//   }

//   getAvailablePresets(): string[] {
//     return Object.keys(this.presets);
//   }

//   getCurrentPreset(): string {
//     return this.config.preset;
//   }

//   // Development helpers
//   exportCurrentConfig(): string {
//     return yaml.dump(this.config, { 
//       indent: 2,
//       lineWidth: 120,
//       noRefs: true 
//     });
//   }

//   debugConfig(): void {
//     console.log('🔧 Current Configuration:');
//     console.log('Enabled pages:', this.getEnabledPages());
//     console.log('Enabled menu items:', this.getEnabledMenuItems());
//     console.log('Floating chat widget:', this.config.components.global.floating_chat_widget);
//     console.log('Full config:', this.config);
//   }
// }

// // Singleton instance
// export const configManager = new ConfigManager();
// export default configManager;