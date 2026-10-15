/**
 * API Client — centralized backend communication with error handling.
 * All requests include the auth token and consistent error responses.
 */

const API_BASE = 'http://localhost:8000/api/v1';

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
        if (v) url.searchParams.set(k, v);
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
  async previewReminder(data: { label: string; scheduled_date: string; scheduled_time: string; recurrence?: string; is_medication?: boolean }) {
    return this.request<any>('POST', '/reminders/preview', { ...data, confirmed: false });
  }

  async createReminder(data: { label: string; scheduled_date: string; scheduled_time: string; recurrence?: string; is_medication?: boolean }) {
    return this.request<any>('POST', '/reminders/', { ...data, confirmed: true });
  }

  async listReminders(date?: string, status?: string, profileId?: string) {
    const params: Record<string, string> = {};
    if (date) params.date = date;
    if (status) params.status = status;
    if (profileId) params.profile_id = profileId;
    return this.request<{ reminders: any[]; total: number }>('GET', '/reminders/', undefined, params);
  }

  async cancelReminder(id: string) {
    return this.request<any>('PATCH', `/reminders/${id}/cancel`);
  }

  async getNextReminder() {
    return this.request<any>('GET', '/reminders/next');
  }

  // Assistant
  async chat(message: string, conversationId?: string) {
    return this.request<any>('POST', '/assistant/chat', {
      message,
      is_voice: false,
      conversation_id: conversationId,
    });
  }

  async confirmReminder(data: any) {
    return this.request<any>('POST', '/assistant/confirm-reminder', data);
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

  async getCheckinConfig() {
    return this.request<any>('GET', '/checkins/config');
  }

  async updateCheckinConfig(data: { enabled?: boolean; time?: string; questions?: string[] }) {
    return this.request<any>('PUT', '/checkins/config', data);
  }

  // Trusted Contacts
  async listContacts() {
    return this.request<any[]>('GET', '/contacts/');
  }

  async createContact(data: { name: string; phone?: string; email?: string; relationship?: string; is_emergency?: boolean }) {
    return this.request<any>('POST', '/contacts/', data);
  }

  async deleteContact(id: string) {
    return this.request<void>('DELETE', `/contacts/${id}`);
  }

  // Help
  async requestHelp(message = '', urgency = 'medium') {
    return this.request<any>('POST', '/help', { message, urgency });
  }

  // Notifications
  async listNotifications(profileId?: string) {
    const params: Record<string, string> = {};
    if (profileId) params.profile_id = profileId;
    return this.request<any[]>('GET', '/notifications', undefined, params);
  }

  // Activity
  async listActivity(profileId?: string) {
    const params: Record<string, string> = {};
    if (profileId) params.profile_id = profileId;
    return this.request<any[]>('GET', '/activity', undefined, params);
  }

  // Caregiver
  async getCaregiverDashboard() {
    return this.request<any>('GET', '/caregiver/dashboard');
  }

  async getSeniorReminders(profileId: string) {
    return this.request<any[]>('GET', `/caregiver/seniors/${profileId}/reminders`);
  }

  async getSeniorCheckins(profileId: string) {
    return this.request<any[]>('GET', `/caregiver/seniors/${profileId}/checkins`);
  }

  async getSeniorNotifications(profileId: string) {
    return this.request<any[]>('GET', `/caregiver/seniors/${profileId}/notifications`);
  }

  async createCaregiverRelationship(seniorProfileId: string, permissions: string[]) {
    return this.request<any>('POST', '/caregiver/relationships', {
      senior_profile_id: seniorProfileId,
      permissions,
    });
  }

  async revokeRelationship(relationshipId: string) {
    return this.request<any>('PATCH', `/caregiver/relationships/${relationshipId}/revoke`);
  }
}

export const api = new ApiClient();
export default api;
