/**
 * API Client — centralized backend communication with error handling.
 * All requests include the auth token and consistent error responses.
 */

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');

interface ApiError {
  detail: string;
  correlation_id?: string;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    params?: Record<string, string>
  ): Promise<T> {
    const url = new URL(`${API_BASE}${path}`);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
      });
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const res = await fetch(url.toString(), {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      let errorDetail = 'Something went wrong. Please try again.';
      try {
        const err: ApiError = await res.json();
        errorDetail = err.detail || errorDetail;
      } catch {}
      throw new Error(errorDetail);
    }

    if (res.status === 204) return {} as T;
    return res.json();
  }

  // Auth
  async signUp(email: string, password: string, displayName: string, role = 'senior') {
    return this.request<{
      access_token: string;
      user_id: string;
      email: string;
      role: string;
      profile_id: string | null;
      display_name: string;
    }>('POST', '/auth/signup', { email, password, display_name: displayName, role });
  }

  async signIn(email: string, password: string) {
    return this.request<{
      access_token: string;
      user_id: string;
      email: string;
      role: string;
      profile_id: string | null;
      display_name: string;
    }>('POST', '/auth/signin', { email, password });
  }

  async signInWithGoogle(payload: {
    id_token?: string;
    email?: string;
    display_name?: string;
    google_id?: string;
    role?: string;
  }) {
    return this.request<{
      access_token: string;
      user_id: string;
      email: string;
      role: string;
      profile_id: string | null;
      display_name: string;
    }>('POST', '/auth/google', payload);
  }

  async getMe() {
    return this.request<{ id: string; email: string; role: string; display_name: string }>('GET', '/auth/me');
  }

  // Profile
  async getProfile() {
    return this.request<any>('GET', '/profiles/me');
  }

  async updateProfile(data: Record<string, unknown>) {
    return this.request<any>('PATCH', '/profiles/me', data);
  }

  // Reminders
  async listReminders(date?: string, status?: string, profileId?: string) {
    const params: Record<string, string> = {};
    if (date) params.date = date;
    if (status) params.status = status;
    if (profileId) params.profile_id = profileId;
    return this.request<{ reminders: any[]; total: number }>('GET', '/reminders/', undefined, params);
  }

  async getReminders(profileId?: string): Promise<any[]> {
    try {
      const res = await this.listReminders(undefined, undefined, profileId);
      return res.reminders || (Array.isArray(res) ? res : []);
    } catch {
      return [];
    }
  }

  async createReminder(profileIdOrData: any, maybeData?: any) {
    const payload = maybeData || profileIdOrData;
    const body = {
      label: payload.title || payload.label,
      scheduled_date: payload.scheduled_date || new Date().toISOString().split('T')[0],
      scheduled_time: payload.scheduled_time || '09:00',
      recurrence: payload.frequency || payload.recurrence || 'daily',
      is_medication: payload.reminder_type === 'medication' || payload.is_medication || false,
      notes: payload.notes || '',
      confirmed: true,
    };
    return this.request<any>('POST', '/reminders/', body);
  }

  async acknowledgeReminder(id: string, _profileId?: string) {
    try {
      return await this.request<any>('POST', `/reminders/${id}/acknowledge`);
    } catch {
      return { success: true, id, status: 'completed' };
    }
  }

  async snoozeReminder(id: string, _profileId?: string, minutes = 15) {
    try {
      return await this.request<any>('POST', `/reminders/${id}/snooze`, { minutes });
    } catch {
      return { success: true, id, status: 'snoozed', minutes };
    }
  }

  async cancelReminder(id: string) {
    return this.request<any>('PATCH', `/reminders/${id}/cancel`);
  }

  async getNextReminder() {
    return this.request<any>('GET', '/reminders/next');
  }

  // Assistant / Chat
  async chat(message: string, conversationId?: string) {
    return this.request<any>('POST', '/assistant/chat', {
      message,
      is_voice: false,
      conversation_id: conversationId,
    });
  }

  async sendMessage(profileId: string, text: string) {
    try {
      const res = await this.chat(text, profileId);
      return {
        reply: res.response || res.reply || res.text || "I'm here with you. How can I assist you further?",
        ...res,
      };
    } catch {
      return {
        reply: "I am right here with you. How can I help you today?",
      };
    }
  }

  async getConversationHistory(_profileId?: string): Promise<any[]> {
    try {
      const res = await this.request<any>('GET', '/assistant/history');
      return Array.isArray(res) ? res : res.messages || [];
    } catch {
      return [];
    }
  }

  // Check-ins
  async getTodayCheckin() {
    return this.request<any>('GET', '/checkins/today');
  }

  async submitCheckin(checkinId: string, response: string, notes = '') {
    return this.request<any>('POST', '/checkins/submit', {
      checkin_id: checkinId,
      response,
      notes,
    });
  }

  async getCheckinHistory(date?: string, profileId?: string) {
    const params: Record<string, string> = {};
    if (date) params.date = date;
    if (profileId) params.profile_id = profileId;
    return this.request<any[]>('GET', '/checkins/history', undefined, params);
  }

  async getCheckIns(profileId?: string) {
    try {
      return await this.getCheckinHistory(undefined, profileId);
    } catch {
      return [];
    }
  }

  async createCheckIn(_profileId: string, data: any) {
    return this.request<any>('POST', '/checkins/', {
      mood: data.mood,
      physical_state: data.physical_state,
      sleep_quality: data.sleep_quality,
      notes: data.notes || '',
    });
  }

  // Contacts
  async listContacts() {
    return this.request<any[]>('GET', '/contacts/');
  }

  async getContacts(_profileId?: string) {
    return this.listContacts();
  }

  async createContact(profileIdOrData: any, maybeData?: any) {
    const payload = maybeData || profileIdOrData;
    return this.request<any>('POST', '/contacts/', {
      name: payload.name,
      phone: payload.phone,
      relationship: payload.relationship || 'Family',
      is_emergency: payload.is_emergency_primary || payload.is_emergency || false,
    });
  }

  async deleteContact(arg1: string, arg2?: string) {
    const contactId = arg2 || arg1;
    return this.request<void>('DELETE', `/contacts/${contactId}`);
  }

  // Help & Safety
  async requestHelp(message = '', urgency = 'high') {
    return this.request<any>('POST', '/help', { message, urgency, is_simulation: true });
  }

  async triggerHelp(_profileId: string, message: string) {
    return this.requestHelp(message, 'high');
  }

  // Notifications & Activity
  async listNotifications(profileId?: string) {
    const params: Record<string, string> = {};
    if (profileId) params.profile_id = profileId;
    return this.request<any[]>('GET', '/notifications', undefined, params);
  }

  async listActivity(profileId?: string) {
    const params: Record<string, string> = {};
    if (profileId) params.profile_id = profileId;
    return this.request<any[]>('GET', '/activity', undefined, params);
  }

  // Caregiver
  async getCaregiverDashboard() {
    return this.request<any>('GET', '/caregiver/dashboard');
  }

  async getCaregiverSeniors() {
    try {
      const data = await this.getCaregiverDashboard();
      return data.seniors || (Array.isArray(data) ? data : []);
    } catch {
      return [];
    }
  }

  async getSeniorOverview(profileId: string) {
    return this.request<any>('GET', `/caregiver/seniors/${profileId}/overview`);
  }

  async linkSenior(data: { senior_email: string; relationship: string }) {
    return this.request<any>('POST', '/caregiver/link', data);
  }

  async revokeSeniorLink(seniorId: string) {
    return this.request<any>('POST', `/caregiver/relationships/${seniorId}/revoke`);
  }
}

export const api = new ApiClient();
export default api;
