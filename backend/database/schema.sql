-- AI For Elders - Database Schema
-- Run this in the Supabase SQL Editor to create all required tables.
-- Uses Supabase Auth for user authentication, with custom tables for app data.

-- ════════════════════════════════════════════════════════
-- USERS TABLE (linked to Supabase Auth)
-- ════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_id UUID UNIQUE NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'senior' CHECK (role IN ('senior', 'caregiver', 'admin')),
    display_name TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_auth_id ON users(auth_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ════════════════════════════════════════════════════════
-- SENIOR PROFILES
-- ════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS senior_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    display_name TEXT DEFAULT '',
    timezone TEXT DEFAULT 'UTC',
    language TEXT DEFAULT 'en',
    speech_rate REAL DEFAULT 1.0,
    high_contrast BOOLEAN DEFAULT FALSE,
    large_text BOOLEAN DEFAULT FALSE,
    onboarding_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_senior_profiles_user_id ON senior_profiles(user_id);

-- ════════════════════════════════════════════════════════
-- CAREGIVER RELATIONSHIPS
-- ════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS caregiver_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    caregiver_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    senior_profile_id UUID NOT NULL REFERENCES senior_profiles(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'pending')),
    permissions JSONB DEFAULT '["view_reminders", "view_checkins"]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(caregiver_user_id, senior_profile_id)
);

CREATE INDEX IF NOT EXISTS idx_caregiver_rel_caregiver ON caregiver_relationships(caregiver_user_id);
CREATE INDEX IF NOT EXISTS idx_caregiver_rel_senior ON caregiver_relationships(senior_profile_id);

-- ════════════════════════════════════════════════════════
-- REMINDERS
-- ════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES senior_profiles(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    scheduled_date TEXT NOT NULL,
    scheduled_time TEXT NOT NULL,
    scheduled_utc TIMESTAMPTZ,
    recurrence TEXT DEFAULT 'none' CHECK (recurrence IN ('none', 'daily', 'weekly')),
    is_medication BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'delivered', 'failed', 'cancelled')),
    created_by UUID REFERENCES users(id),
    idempotency_key TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminders_profile ON reminders(profile_id);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);
CREATE INDEX IF NOT EXISTS idx_reminders_date ON reminders(scheduled_date);

-- ════════════════════════════════════════════════════════
-- CHECK-INS
-- ════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES senior_profiles(id) ON DELETE CASCADE,
    scheduled_time TEXT NOT NULL,
    scheduled_date TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'missed', 'escalated')),
    response TEXT CHECK (response IN ('okay', 'skip', 'need_help', NULL)),
    notes TEXT DEFAULT '',
    escalated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    responded_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_checkins_profile ON checkins(profile_id);
CREATE INDEX IF NOT EXISTS idx_checkins_date ON checkins(scheduled_date);

-- ════════════════════════════════════════════════════════
-- CHECK-IN CONFIGURATION
-- ════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS checkin_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES senior_profiles(id) ON DELETE CASCADE UNIQUE,
    enabled BOOLEAN DEFAULT TRUE,
    time TEXT DEFAULT '09:00',
    questions JSONB DEFAULT '["How are you feeling today?"]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════════════════════
-- TRUSTED CONTACTS
-- ════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS trusted_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES senior_profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT DEFAULT '',
    email TEXT DEFAULT '',
    relationship TEXT DEFAULT '',
    is_emergency BOOLEAN DEFAULT FALSE,
    notify_on_help BOOLEAN DEFAULT TRUE,
    notify_on_missed_checkin BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trusted_contacts_profile ON trusted_contacts(profile_id);

-- ════════════════════════════════════════════════════════
-- NOTIFICATIONS
-- ════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES senior_profiles(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('reminder', 'checkin', 'help', 'escalation')),
    message TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'simulated')),
    is_simulated BOOLEAN DEFAULT TRUE,
    recipient TEXT DEFAULT '',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notifications_profile ON notifications(profile_id);

-- ════════════════════════════════════════════════════════
-- AUDIT EVENTS
-- ════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES senior_profiles(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_profile ON audit_events(profile_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type);

-- ════════════════════════════════════════════════════════
-- CONVERSATIONS (lightweight tracking)
-- ════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES senior_profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    intent TEXT,
    action_taken TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversation_turns_conv ON conversation_turns(conversation_id);

-- ════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY (RLS) - Enable on all tables
-- ════════════════════════════════════════════════════════
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE senior_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE caregiver_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkins ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkin_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE trusted_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_turns ENABLE ROW LEVEL SECURITY;

-- Allow service_role full access (our backend uses service_role key)
-- The backend enforces authorization itself.
CREATE POLICY "service_role_all" ON users FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON senior_profiles FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON caregiver_relationships FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON reminders FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON checkins FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON checkin_configs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON trusted_contacts FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON notifications FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON audit_events FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON conversations FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON conversation_turns FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Allow anon/authenticated users to interact via Supabase Auth (for frontend direct auth)
CREATE POLICY "users_own" ON users FOR SELECT TO authenticated USING (auth_id = auth.uid());
CREATE POLICY "profiles_own" ON senior_profiles FOR SELECT TO authenticated 
    USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));
