/* ==========================================================================
   Vridhi Parent Analytics — app.js
   API client + Chart.js defaults + fallback data engine.
   Works whether served by Django (http://.../dashboard.html) or opened
   directly as a local file (file://.../dashboard.html).
   ========================================================================== */

const API_BASE = (typeof window !== 'undefined' && window.location.protocol.startsWith('http'))
  ? '/api'
  : 'http://127.0.0.1:8000/api';

const VRIDHI_COLORS = {
  ink: '#16223b',
  inkSoft: '#3a4a68',
  marigold: '#e8a33d',
  leaf: '#2f7a55',
  brick: '#b24438',
  sky: '#3d6b8c',
  line: '#dde2d8',
};

if (window.Chart) {
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.color = VRIDHI_COLORS.inkSoft;
  Chart.defaults.borderColor = VRIDHI_COLORS.line;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
}

// ---------------------------------------------------------------------------
// Small fetch helper
// ---------------------------------------------------------------------------

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, { headers: { 'Accept': 'application/json' } });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Fallback demo data (used if the Django backend is unreachable)
// ---------------------------------------------------------------------------

function _demoDates(n, stepDays) {
  const out = [];
  const today = new Date();
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i * stepDays);
    out.push(d.toISOString().slice(0, 10));
  }
  return out;
}

function fallbackStudents() {
  return [{ id: 1, name: 'Aarav Shah', grade: '8', class: 'B', school: 'Vridhi Demo School' }];
}

function fallbackChildProgress() {
  const dates = _demoDates(8, 14);
  const academic = ['Math', 'Science', 'English', 'Social Studies'];
  const academic_timeline = [];
  dates.forEach((d, i) => {
    academic.forEach((subj, j) => {
      academic_timeline.push({ date: d, subject: subj, score: Math.round(55 + i * 2.5 + j * 4 + (Math.random() * 6 - 3)) });
    });
  });
  const emotional_timeline = _demoDates(12, 7).map((d, i) => ({
    date: d,
    mood_score: Math.round((5.8 + i * 0.05 + (Math.random() * 1.2 - 0.6)) * 10) / 10,
    mood_label: i === 4 || i === 5 ? 'stressed' : 'stable',
    sleep_hours: Math.round((7.1 + (Math.random() * 0.8 - 0.4)) * 10) / 10,
  }));
  return {
    student: { id: 1, name: 'Aarav Shah', grade: '8', class: 'B', school: 'Vridhi Demo School' },
    growth_snapshot: {
      growth_score: 67.1,
      phase: 'Steady Growth',
      academic_average: 68.8,
      wellbeing_average: 6.3,
      academic_trend: 'up',
      wellbeing_trend: 'flat',
      wellbeing_academic_correlation: 0.12,
    },
    academic_timeline,
    emotional_timeline,
    critical_events: [
      { date: dates[3], type: 'wellbeing_dip', description: 'Wellbeing dropped to 3.4/10 (stressed).' },
    ],
    insights: [
      'Wellbeing and academics are moving independently right now.',
      'Academic performance is trending upward over the recent period.',
    ],
    _offline: true,
  };
}

function fallbackParentImpact() {
  return {
    student_id: 1,
    parent_impact_score: 72.6,
    optimal_band: { low: 55, high: 85 },
    communication_effectiveness: 'positive',
    impact_by_activity: [
      { activity_type: 'routine_check_in', sessions: 8, total_minutes: 210 },
      { activity_type: 'reading_together', sessions: 8, total_minutes: 205 },
      { activity_type: 'praise_encouragement', sessions: 9, total_minutes: 185 },
      { activity_type: 'outdoor_play', sessions: 8, total_minutes: 175 },
      { activity_type: 'parent_teacher_chat', sessions: 3, total_minutes: 80 },
      { activity_type: 'screen_time_limit', sessions: 3, total_minutes: 75 },
      { activity_type: 'homework_help', sessions: 3, total_minutes: 75 },
    ],
    behavior_signal: 'Engagement sits within the optimal band. Keep the current rhythm going.',
    total_engagement_minutes: 1005,
    total_sessions: 42,
    _offline: true,
  };
}

function fallbackHomeSupport() {
  return {
    student_id: 1,
    learning_profile: {
      strongest_subject: 'English',
      weakest_subject: 'Math',
      average_wellbeing: 6.3,
      average_sleep_hours: 7.0,
      learning_style_note: 'Generally steady, but benefits from consistent encouragement.',
    },
    do_and_dont: [
      { type: 'do', text: 'Break problems into smaller steps and celebrate each correct step.', subject: 'Math' },
      { type: 'dont', text: "Don't rush through problem sets against the clock — it raises anxiety.", subject: 'Math' },
      { type: 'do', text: 'Keep a predictable daily routine and consistent bedtime.', subject: 'general' },
    ],
    weekly_home_plan: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day, i) => ({
      day,
      focus: i < 5 ? (i % 2 === 0 ? 'Math' : 'English') : 'Rest & Connection',
      activity: i < 5
        ? `20-30 min focused practice on ${i % 2 === 0 ? 'Math' : 'English'}, followed by 10 min of parent check-in.`
        : 'Light review, outdoor play, and quality family time — no formal study pressure.',
    })),
    risk_alert: null,
    mentor_tip: 'Small, consistent daily engagement beats occasional long study sessions — aim for short, positive touchpoints rather than pressure-filled marathons.',
    _offline: true,
  };
}

// ---------------------------------------------------------------------------
// Public fetch functions (try live API, fall back to demo data)
// ---------------------------------------------------------------------------

async function fetchStudents() {
  try {
    return await apiGet('/students/');
  } catch (e) {
    console.warn('Falling back to demo student list:', e.message);
    return fallbackStudents();
  }
}

async function fetchChildProgress(studentId) {
  try {
    return await apiGet(`/students/${studentId}/reports/child-progress/`);
  } catch (e) {
    console.warn('Falling back to demo child-progress data:', e.message);
    return fallbackChildProgress();
  }
}

async function fetchParentImpact(studentId) {
  try {
    return await apiGet(`/students/${studentId}/reports/parent-impact/`);
  } catch (e) {
    console.warn('Falling back to demo parent-impact data:', e.message);
    return fallbackParentImpact();
  }
}

async function fetchHomeSupport(studentId) {
  try {
    return await apiGet(`/students/${studentId}/reports/home-support/`);
  } catch (e) {
    console.warn('Falling back to demo home-support data:', e.message);
    return fallbackHomeSupport();
  }
}

// ---------------------------------------------------------------------------
// Shared UI helpers
// ---------------------------------------------------------------------------

function activityLabel(key) {
  const map = {
    homework_help: 'Homework Help',
    reading_together: 'Reading Together',
    screen_time_limit: 'Screen Time Limit',
    parent_teacher_chat: 'Parent-Teacher Chat',
    outdoor_play: 'Outdoor Play',
    praise_encouragement: 'Praise & Encouragement',
    routine_check_in: 'Routine Check-in',
  };
  return map[key] || key;
}

function phaseTagClass(phase) {
  if (phase === 'Accelerating') return 'tag-leaf';
  if (phase === 'Steady Growth') return 'tag-sky';
  if (phase === 'Needs Support') return 'tag-marigold';
  return 'tag-brick';
}

function renderGrowthRing(el, score, label) {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;
  el.innerHTML = `
    <div class="growth-ring-wrap">
      <svg viewBox="0 0 168 168">
        <circle class="growth-ring-track" cx="84" cy="84" r="${radius}" stroke-width="14"></circle>
        <circle class="growth-ring-fill" cx="84" cy="84" r="${radius}" stroke-width="14"
          stroke-dasharray="${circumference}" stroke-dashoffset="${circumference}"></circle>
      </svg>
      <div class="growth-ring-center">
        <div class="num">${Math.round(score)}</div>
        <div class="lbl">${label || 'Growth Score'}</div>
      </div>
    </div>`;
  requestAnimationFrame(() => {
    const fill = el.querySelector('.growth-ring-fill');
    if (fill) fill.style.strokeDashoffset = String(offset);
  });
}

function getSelectedStudentId() {
  return Number(localStorage && window.__vridhiStudentId ? window.__vridhiStudentId : 1) || 1;
}

// Simple in-memory (non-persisted) "current student" — avoids localStorage
// per platform constraints; defaults to the demo student.
window.__vridhiStudentId = window.__vridhiStudentId || 1;

function markActiveNav() {
  const path = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.side-nav a, .nav-links a').forEach((a) => {
    const href = a.getAttribute('href');
    if (href === path || (path === '' && href === 'index.html')) {
      a.classList.add('active');
    }
  });
}

document.addEventListener('DOMContentLoaded', markActiveNav);
