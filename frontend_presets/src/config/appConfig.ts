// frontend/src/config/appConfig.ts
// Simple configuration - just change the preset name to switch features

export type PresetName = 'basic' | 'call-only' | 'chat-only' | 'full';

// ⭐ CHANGE THIS LINE TO SWITCH PRESETS ⭐
const CURRENT_PRESET: PresetName = 'basic';

// Configuration interface
interface AppConfig {
  preset: string;
  pages: {
    signin: boolean;
    dashboard: boolean;
    call_test: boolean;
    call_history: boolean;
    chat_history: boolean;
    feedback: boolean;
  };
  components: {
    header: {
      dashboard_menu: boolean;
      call_test_menu: boolean;
      call_history_menu: boolean;
      feedback_menu: boolean;
      user_avatar_dropdown: boolean;
    };
    call_test: {
      tryout_component: boolean;
      talk_to_vaani_component: boolean;
      talk_to_vaani: {
        name_field: boolean;
        country_code_selector: boolean;
        phone_number_field: boolean;
        voice_selection: boolean;
        voice_options_dropdown: boolean;
        use_case_dropdown: boolean;
        trigger_call_button: boolean;
      };
    };
    call_history: {
      view_mode_toggle: boolean;
      filters_section: boolean;
      search_functionality: boolean;
      date_range_filter: boolean;
      status_filter: boolean;
      direction_filter: boolean;
      selection_checkboxes: boolean;
      bulk_operations: boolean;
      csv_download: boolean;
      call_details_sidebar: {
        audio_recording: boolean;
        transcript_section: boolean;
        summary_section: boolean;
        conversation_evaluation: boolean;
        entity_extraction: boolean;
      };
    };
    dashboard: {
      call_metrics: boolean;
      chat_metrics: boolean;
      period_toggle: boolean;
      metrics_cards: boolean;
      call_trends_chart: boolean;
      chat_trends_chart: boolean;
      duration_chart: boolean;
    };
    feedback: {
      rating_sliders: boolean;
      feedback_text_area: boolean;
      submit_button: boolean;
    };
    global: {
      floating_chat_widget: boolean;
      footer: boolean;
    };
  };
}

// Preset configurations
const PRESETS: Record<PresetName, AppConfig> = {
  basic: {
    preset: 'basic',
    pages: {
      signin: true,
      dashboard: false,
      call_test: true,
      call_history: true,
      chat_history: false,
      feedback: true,
    },
    components: {
      header: {
        dashboard_menu: false,
        call_test_menu: true,
        call_history_menu: true,
        feedback_menu: true,
        user_avatar_dropdown: true,
      },
      call_test: {
        tryout_component: true,
        talk_to_vaani_component: true,
        talk_to_vaani: {
          name_field: true,
          country_code_selector: true,
          phone_number_field: true,
          voice_selection: false,  // No voice options in basic
          voice_options_dropdown: false,
          use_case_dropdown: true,
          trigger_call_button: true,
        },
      },
      call_history: {
        view_mode_toggle: false,
        filters_section: false,  // No filters in basic
        search_functionality: false,
        date_range_filter: false,
        status_filter: false,
        direction_filter: false,
        selection_checkboxes: false,  // No selection in basic
        bulk_operations: false,
        csv_download: false,  // No download in basic
        call_details_sidebar: {
          audio_recording: false,  // No audio in basic
          transcript_section: true,
          summary_section: true,
          conversation_evaluation: false,  // No evaluation in basic
          entity_extraction: false,  // No extraction in basic
        },
      },
      dashboard: {
        call_metrics: false,
        chat_metrics: false,
        period_toggle: false,
        metrics_cards: false,
        call_trends_chart: false,
        chat_trends_chart: false,
        duration_chart: false,
      },
      feedback: {
        rating_sliders: true,
        feedback_text_area: true,
        submit_button: true,
      },
      global: {
        floating_chat_widget: false,  // No chat in basic
        footer: true,
      },
    },
  },

  'call-only': {
    preset: 'call-only',
    pages: {
      signin: true,
      dashboard: true,
      call_test: true,
      call_history: true,
      chat_history: false,
      feedback: true,
    },
    components: {
      header: {
        dashboard_menu: true,
        call_test_menu: true,
        call_history_menu: true,
        feedback_menu: true,
        user_avatar_dropdown: true,
      },
      call_test: {
        tryout_component: true,
        talk_to_vaani_component: true,
        talk_to_vaani: {
          name_field: true,
          country_code_selector: true,
          phone_number_field: true,
          voice_selection: true,  // Voice options enabled
          voice_options_dropdown: true,
          use_case_dropdown: true,
          trigger_call_button: true,
        },
      },
      call_history: {
        view_mode_toggle: false,  // Only calls, no toggle needed
        filters_section: true,
        search_functionality: true,
        date_range_filter: true,
        status_filter: true,
        direction_filter: true,
        selection_checkboxes: true,
        bulk_operations: true,
        csv_download: true,
        call_details_sidebar: {
          audio_recording: true,
          transcript_section: true,
          summary_section: true,
          conversation_evaluation: true,
          entity_extraction: true,
        },
      },
      dashboard: {
        call_metrics: true,  // Only call metrics
        chat_metrics: false,
        period_toggle: true,
        metrics_cards: true,
        call_trends_chart: true,
        chat_trends_chart: false,
        duration_chart: true,
      },
      feedback: {
        rating_sliders: true,
        feedback_text_area: true,
        submit_button: true,
      },
      global: {
        floating_chat_widget: false,  // No chat widget
        footer: true,
      },
    },
  },

  'chat-only': {
    preset: 'chat-only',
    pages: {
      signin: true,
      dashboard: true,
      call_test: false,  // No call test page
      call_history: false,
      chat_history: true,
      feedback: true,
    },
    components: {
      header: {
        dashboard_menu: true,
        call_test_menu: false,  // No call test menu
        call_history_menu: false,
        feedback_menu: true,
        user_avatar_dropdown: true,
      },
      call_test: {
        tryout_component: false,
        talk_to_vaani_component: false,
        talk_to_vaani: {
          name_field: false,
          country_code_selector: false,
          phone_number_field: false,
          voice_selection: false,
          voice_options_dropdown: false,
          use_case_dropdown: false,
          trigger_call_button: false,
        },
      },
      call_history: {
        view_mode_toggle: false,
        filters_section: false,
        search_functionality: false,
        date_range_filter: false,
        status_filter: false,
        direction_filter: false,
        selection_checkboxes: false,
        bulk_operations: false,
        csv_download: false,
        call_details_sidebar: {
          audio_recording: false,
          transcript_section: false,
          summary_section: false,
          conversation_evaluation: false,
          entity_extraction: false,
        },
      },
      dashboard: {
        call_metrics: false,
        chat_metrics: true,  // Only chat metrics
        period_toggle: true,
        metrics_cards: true,
        call_trends_chart: false,
        chat_trends_chart: true,
        duration_chart: false,
      },
      feedback: {
        rating_sliders: true,
        feedback_text_area: true,
        submit_button: true,
      },
      global: {
        floating_chat_widget: true,  // Chat widget enabled
        footer: true,
      },
    },
  },

  full: {
    preset: 'full',
    pages: {
      signin: true,
      dashboard: true,
      call_test: true,
      call_history: true,
      chat_history: true,
      feedback: true,
    },
    components: {
      header: {
        dashboard_menu: true,
        call_test_menu: true,
        call_history_menu: true,
        feedback_menu: true,
        user_avatar_dropdown: true,
      },
      call_test: {
        tryout_component: true,
        talk_to_vaani_component: true,
        talk_to_vaani: {
          name_field: true,
          country_code_selector: true,
          phone_number_field: true,
          voice_selection: true,
          voice_options_dropdown: true,
          use_case_dropdown: true,
          trigger_call_button: true,
        },
      },
      call_history: {
        view_mode_toggle: true,  // calls/chats/all toggle
        filters_section: true,
        search_functionality: true,
        date_range_filter: true,
        status_filter: true,
        direction_filter: true,
        selection_checkboxes: true,
        bulk_operations: true,
        csv_download: true,
        call_details_sidebar: {
          audio_recording: true,
          transcript_section: true,
          summary_section: true,
          conversation_evaluation: true,
          entity_extraction: true,
        },
      },
      dashboard: {
        call_metrics: true,
        chat_metrics: true,
        period_toggle: true,
        metrics_cards: true,
        call_trends_chart: true,
        chat_trends_chart: true,
        duration_chart: true,
      },
      feedback: {
        rating_sliders: true,
        feedback_text_area: true,
        submit_button: true,
      },
      global: {
        floating_chat_widget: true,
        footer: true,
      },
    },
  },
};

// Get current configuration
export const CONFIG = PRESETS[CURRENT_PRESET];

// Helper functions
export const isPageEnabled = (page: keyof AppConfig['pages']): boolean => {
  return CONFIG.pages[page];
};

export const isComponentEnabled = (path: string): boolean => {
  const parts = path.split('.');
  let current: any = CONFIG.components;
  
  for (const part of parts) {
    if (current[part] === undefined) {
      return false;
    }
    current = current[part];
  }
  
  return current === true;
};

// Page paths - only include enabled pages
export const pagePaths = {
  ...(CONFIG.pages.signin && { signin: '/sign-in' }),
  ...(CONFIG.pages.call_test && { landing: '/', home: '/home' }),
  ...(CONFIG.pages.dashboard && { dashboard: '/dashboard' }),
  ...(CONFIG.pages.call_history && { history: '/history' }),
  ...(CONFIG.pages.feedback && { feedback: '/feedback' }),
};

// Menu items - only include enabled items
export const menuItems = [
  ...(CONFIG.components.header.dashboard_menu && CONFIG.pages.dashboard ? [{ 
    label: "Dashboard", 
    icon: "pi pi-chart-bar", 
    url: "/dashboard" 
  }] : []),
  ...(CONFIG.components.header.call_test_menu && CONFIG.pages.call_test ? [{ 
    label: "Call Test", 
    icon: "pi pi-phone", 
    url: "/home" 
  }] : []),
  ...(CONFIG.components.header.call_history_menu && CONFIG.pages.call_history ? [{ 
    label: "Call History", 
    icon: "pi pi-history", 
    url: "/history" 
  }] : []),
  ...(CONFIG.components.header.feedback_menu && CONFIG.pages.feedback ? [{ 
    label: "Feedback", 
    icon: "pi pi-comment", 
    url: "/feedback" 
  }] : []),
];

// Debug info (remove in production)
if (process.env.NODE_ENV === 'development') {
  console.log(`🔧 Current preset: ${CONFIG.preset}`);
  console.log('📄 Enabled pages:', Object.entries(CONFIG.pages).filter(([, enabled]) => enabled).map(([page]) => page));
}