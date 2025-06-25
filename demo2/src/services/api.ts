// API service for communication with Flask backend

const API_BASE_URL = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:5001';

class ApiService {
  private credentials = {
    username: 'admin',
    password: 'password' // This should match your AUTH_PASSWORD in .env
  };

  updateCredentials(username: string, password: string) {
    this.credentials = { username, password };
  }

  private getAuthHeaders(): HeadersInit {
    const credentials = btoa(`${this.credentials.username}:${this.credentials.password}`);
    return {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${credentials}`
    };
  }

  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Dashboard APIs
  async getDashboardMetrics() {
    return this.makeRequest<{
      metrics: {
        total_calls: { value: number; change: number };
        appointments_booked: { value: number; change: number };
        avg_call_duration: { value: string; change: number };
        live_calls: { value: number };
      };
      performance: {
        answer_rate: number;
        booking_rate: number;
        miss_rate: number;
      };
    }>('/api/dashboard/metrics');
  }

  async getRecentCalls(limit: number = 10) {
    return this.makeRequest<{
      recent_calls: Array<{
        id: number;
        caller: string;
        time: string;
        duration: string;
        type: 'AI' | 'Human-Human';
        status: 'answered' | 'missed' | 'booked';
        call_sid: string;
      }>;
    }>(`/api/dashboard/recent-calls?limit=${limit}`);
  }

  async getSystemStatus() {
    return this.makeRequest<{
      system_status: {
        voice_ai: { status: 'operational' | 'issue'; message: string };
        call_recording: { status: 'operational' | 'issue'; message: string };
        calendar_sync: { status: 'operational' | 'issue'; message: string };
      };
    }>('/api/dashboard/system-status');
  }

  // Call APIs
  async getCalls(page: number = 1, perPage: number = 50, status?: string) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString()
    });
    
    if (status) {
      params.append('status', status);
    }

    return this.makeRequest<{
      calls: Array<{
        id: number;
        call_sid: string;
        from_number: string;
        to_number: string;
        status: string;
        start_time: string;
        end_time?: string;
        duration?: number;
        call_type: string;
        transcript_count: number;
        interaction_count: number;
      }>;
      total: number;
      pages: number;
      current_page: number;
    }>(`/api/calls?${params.toString()}`);
  }

  async getCallDetails(callId: number) {
    return this.makeRequest<{
      id: number;
      call_sid: string;
      from_number: string;
      to_number: string;
      status: string;
      start_time: string;
      end_time?: string;
      duration?: number;
      call_type: string;
      transcripts: Array<{
        id: number;
        timestamp: string;
        speaker: string;
        text: string;
        confidence: number;
        is_final: boolean;
      }>;
      interactions: Array<{
        id: number;
        timestamp: string;
        intent: string;
        confidence: number;
        user_input: string;
        ai_response: string;
        action_taken?: string;
      }>;
      appointments: Array<{
        id: number;
        title: string;
        start_time: string;
        end_time: string;
        attendee_email?: string;
        attendee_phone?: string;
        status: string;
      }>;
      summary?: string;
    }>(`/api/calls/${callId}`);
  }

  // Appointment APIs
  async getAppointments(page: number = 1, perPage: number = 50) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString()
    });

    return this.makeRequest<{
      appointments: Array<{
        id: number;
        title: string;
        description?: string;
        start_time: string;
        end_time: string;
        attendee_email?: string;
        attendee_phone?: string;
        status: string;
        created_at: string;
        google_event_id?: string;
      }>;
      total: number;
      pages: number;
      current_page: number;
    }>(`/api/appointments?${params.toString()}`);
  }

  async bookAppointment(appointmentData: {
    title: string;
    description?: string;
    start_time: string;
    end_time: string;
    attendee_email?: string;
    attendee_phone?: string;
  }) {
    return this.makeRequest<{
      id: number;
      title: string;
      start_time: string;
      end_time: string;
      status: string;
    }>('/api/book-appointment', {
      method: 'POST',
      body: JSON.stringify(appointmentData)
    });
  }

  async getAvailableSlots(date: string, duration: number = 30) {
    const params = new URLSearchParams({
      date,
      duration: duration.toString()
    });

    return this.makeRequest<{
      available_slots: Array<{
        start: string;
        end: string;
        duration: number;
      }>;
    }>(`/api/available-slots?${params.toString()}`);
  }

  // CRM APIs
  async triggerCrmWebhook(webhookUrl: string, payload: any, callId?: number) {
    return this.makeRequest<{
      success: boolean;
      status_code?: number;
      webhook_id?: number;
      response?: string;
      error?: string;
    }>('/api/crm-trigger', {
      method: 'POST',
      body: JSON.stringify({
        webhook_url: webhookUrl,
        payload,
        call_id: callId
      })
    });
  }

  // Health check
  async getHealth() {
    return this.makeRequest<{
      status: string;
      timestamp: string;
    }>('/health');
  }
}

export const apiService = new ApiService();
export default apiService;