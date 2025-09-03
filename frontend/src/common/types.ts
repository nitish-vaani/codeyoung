// export type CreateUserRequest = {
//     user_id: string,
//     username: string,
//     contact_number: string,
//     password: string
//   }

// export type LoginRequest = { username: string, password: string }

// export type LoginResponse = { message: string, user_id: string }

// export type TriggerCallRequest = {
//         user_id: string,
//         agent_id: string,
//         name: string,
//         contact_number: string,
//         voice?: string
// }

// export type FeedbackRequest = {
//     conversation_id: string,
//     user_id: string,
//     feedback_text: string,
//     felt_natural: number,
//     response_speed: number,
//     interruptions: number,
// }

// // Dashboard types
// export type DashboardMetrics = {
//     total_calls: number,
//     total_leads: number,
//     conversion_rate: number,
//     avg_call_duration: number
// }

// export type TrendData = {
//     date: string,
//     calls: number,
//     leads: number,
//     duration: number
// }

// export type DashboardResponse = {
//     metrics: DashboardMetrics,
//     call_trends: TrendData[],
//     lead_trends: TrendData[],
//     period: string
// }



// frontend/src/common/types.ts
export type CreateUserRequest = {
    user_id: string,
    username: string,
    contact_number: string,
    password: string
  }

export type LoginRequest = { username: string, password: string }

export type LoginResponse = { message: string, user_id: string }

export type TriggerCallRequest = {
        user_id: string,
        agent_id: string,
        name: string,
        contact_number: string,
        voice?: string
}

export type FeedbackRequest = {
    conversation_id: string,
    user_id: string,
    feedback_text: string,
    felt_natural: number,
    response_speed: number,
    interruptions: number,
}

// NEW: Chat types
export type TriggerChatRequest = {
    user_id: string,
    agent_id: string,
    name: string,
    agent_name: string,
    session_id?: string
}

export type ChatTokenRequest = {
    room_id: string,
    user_name: string
}

export type ChatMessage = {
    id: string,
    type: 'user' | 'agent' | 'system',
    content: string,
    timestamp: Date,
    sender: string
}

// Dashboard types
export type DashboardMetrics = {
    total_calls: number,
    total_leads: number,
    conversion_rate: number,
    avg_call_duration: number
}

export type TrendData = {
    date: string,
    calls: number,
    leads: number,
    duration: number
}

export type DashboardResponse = {
    metrics: DashboardMetrics,
    call_trends: TrendData[],
    lead_trends: TrendData[],
    period: string
}