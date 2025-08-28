import axios from "axios"
import { CreateUserRequest, FeedbackRequest, LoginRequest, TriggerCallRequest, DashboardResponse } from "./types"

// Single base URL for the merged API (running on port 1234)
axios.defaults.baseURL = `https://codeyoung-bk.vaaniresearch.com/api`

const client = "code" // This is the client name used in the API calls;

export const voiceOptions = [
  { label: 'Default', value: '', gender: 'N/A' },
  { label: 'English Indian(M)-1', value: 'English Indian(M)-1', gender: 'M' },
  { label: 'English Indian(F)-1', value: 'English Indian(F)-1', gender: 'F' },
  { label: 'English US(M)-1', value: 'English US(M)-1', gender: 'M' },
  { label: 'English US(M)-2', value: 'English US(M)-2', gender: 'M' },
  { label: 'English US(F)-1', value: 'English US(F)-1', gender: 'F' },
  { label: 'English US(F)-2', value: 'English US(F)-2', gender: 'F' }
];

export const maleVoices = voiceOptions.filter(voice => voice.gender === 'M');
export const femaleVoices = voiceOptions.filter(voice => voice.gender === 'F');

export const CreateUser = (user: CreateUserRequest) => {
  return axios.post('/users/', user, {
    timeout: 20000
  })
}

export const loginUser = (loginReq: LoginRequest) => {
  return axios.post('/login/', loginReq, {
    timeout: 20000
  })
}

export const getAllModels = () => {
  return axios.get(`/models/${client}`, {
    timeout: 20000
  })
}

export const triggerCall = (callReq: TriggerCallRequest) => {
  return axios.post('/trigger-call/', callReq, {
    timeout: 20000
  })
}

export const getCallHistory = (user_id: string) => {
  return axios.get(`/call-history/${user_id}/${client}`, {
    timeout: 20000
  });
}

export const submitFeedback = (callReq: FeedbackRequest) => {
  return axios.post('/submit-feedback/', callReq, {
    timeout: 20000
  })
}

export const getCallDetails = (user_id: string, conversation_id: string) => {
  return axios.get(`/call_details/${client}/${user_id}/${conversation_id}`, {
    timeout: 20000
  })
}

export const getRecStream = async (conversation_id: string) => {
  try {
    const response = await axios.get(`/stream/${conversation_id}`, {
      responseType: "blob",  // Ensures correct audio format
      timeout: 20000
    });

    const audioUrl = URL.createObjectURL(response.data);
    return audioUrl;
  } catch (error) {
    console.error("Error fetching recording:", error);
    return null;
  }
};

// Dashboard API calls - now using the same base URL
export const getDashboardData = (user_id: string, period: string = "7_days"): Promise<{ data: DashboardResponse }> => {
  return axios.get(`/dashboard`, {
    params: {
      user_id,
      client,
      period
    },
    timeout: 20000
  });
};

export const getDashboardSummary = (user_id: string) => {
  return axios.get(`/dashboard/summary`, {
    params: {
      user_id,
      client
    },
    timeout: 20000
  });
};