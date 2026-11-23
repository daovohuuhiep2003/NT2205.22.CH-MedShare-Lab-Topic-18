<template>
  <!-- Wait for initial session check -->
  <div v-if="checkingSession" class="min-h-screen flex items-center justify-center text-sm transition-colors duration-200"
       :class="isDark ? 'bg-slate-950 text-slate-300' : 'bg-slate-100 text-slate-600'">
    <div class="flex items-center space-x-2">
      <svg class="animate-spin h-5 w-5 text-teal-600" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span>Đang kết nối phiên làm việc Cổng Bệnh án Điện tử...</span>
    </div>
  </div>

  <!-- Unauthenticated -> Login Screen -->
  <LoginView
    v-else-if="!currentUser"
    :isDark="isDark"
    @toggle-theme="toggleTheme"
    @authenticated="handleAuthenticated"
  />

  <!-- Authenticated Portal -->
  <div v-else class="min-h-screen flex flex-col font-sans transition-colors duration-200"
       :class="isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-100/80 text-slate-800'">
    <Navbar
      :user="currentUser"
      :isDark="isDark"
      @toggle-theme="toggleTheme"
      @logout="handleLogout"
      @password-changed="handleLogout"
    />

    <!-- Navigation Tabs (Hospital Department Modules) -->
    <div class="border-b transition-colors duration-200 no-print"
         :class="isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white shadow-xs'">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-1.5 overflow-x-auto py-2">
        <button
          v-for="tab in visibleTabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'flex items-center space-x-2 px-3.5 py-2 text-xs font-semibold rounded-xl whitespace-nowrap transition-all',
            activeTab === tab.id
              ? (isDark
                  ? 'bg-teal-500/15 text-teal-400 border border-teal-500/30 shadow-xs'
                  : 'bg-teal-50 text-teal-800 border border-teal-200 shadow-xs font-bold')
              : (isDark
                  ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent')
          ]"
        >
          <span>{{ tab.label }}</span>
          <span
            v-if="tab.badge"
            class="px-1.5 py-0.5 text-[10px] rounded font-mono"
            :class="isDark ? 'bg-slate-800 text-slate-300' : 'bg-slate-200 text-slate-700'"
          >
            {{ tab.badge }}
          </span>
        </button>
      </div>
    </div>

    <!-- Main Content Area -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5">
      <!-- Role Context Info Banner (Duty Station Banner) -->
      <div
        v-if="currentUser"
        class="mb-5 p-3.5 rounded-2xl border transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs no-print"
        :class="isDark
          ? 'bg-slate-900/80 border-slate-800 text-slate-300'
          : 'bg-white border-slate-200 text-slate-700 shadow-xs'"
      >
        <div class="flex flex-wrap items-center gap-2.5">
          <span class="px-2.5 py-1 rounded-lg font-bold border text-[11px] uppercase tracking-wide"
                :class="isDark
                  ? 'bg-teal-500/15 text-teal-400 border-teal-500/30'
                  : 'bg-teal-50 text-teal-800 border-teal-200'">
            {{ currentUser.role }}
          </span>
          <span class="font-bold text-slate-900 dark:text-white">{{ currentUser.full_name }}</span>
          <span v-if="currentUser.title" class="text-slate-500 dark:text-slate-400 hidden md:inline">
            — {{ currentUser.title }}
          </span>
        </div>
        <div class="text-[11px] font-mono text-slate-500 dark:text-slate-400 flex flex-wrap items-center gap-2">
          <span>Khoa: <strong class="text-teal-700 dark:text-teal-300">{{ currentUser.department }}</strong></span>
          <span>·</span>
          <span>Cơ sở: <strong class="text-slate-800 dark:text-slate-200">{{ currentUser.tenant_id }}</strong></span>
          <span>·</span>
          <span>ID: <code class="text-slate-700 dark:text-slate-300">{{ currentUser.user_id }}</code></span>
        </div>
      </div>

      <!-- Tab Panels -->
      <AccountsTab
        v-if="activeTab === 'accounts'"
        :currentUsername="currentUser.username"
        :isDark="isDark"
      />

      <div v-else-if="activeTab === 'patients'" class="space-y-4">
        <div
          v-if="patientsResponse.status === 'DENIED'"
          class="p-4 rounded-xl bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 text-amber-800 dark:text-amber-200 text-xs"
        >
          <span class="font-bold text-amber-700 dark:text-amber-400">Thông báo phân quyền:</span>
          Tài khoản hiện tại không thuộc diện phân công quản lý hồ sơ bệnh án lâm sàng.
        </div>
        <PatientsTab
          :patients="patientsResponse.records || []"
          :currentRole="currentUser.role"
          :currentUser="currentUser"
          :isDark="isDark"
          @refresh="loadPatients"
          @toast="showToast"
        />
      </div>

      <AttachmentsTab
        v-else-if="activeTab === 'attachments'"
        :patients="patientsResponse.records || []"
        :currentRole="currentUser.role"
        :currentUser="currentUser"
        :isDark="isDark"
        @toast="showToast"
      />

      <CryptoTab
        v-else-if="activeTab === 'crypto'"
        :patients="patientsResponse.records || []"
        :currentUser="currentUser"
        :isDark="isDark"
        @toast="showToast"
      />

      <DbaAuditTab
        v-else-if="activeTab === 'dba'"
        :isDark="isDark"
      />

      <AuditLogTab
        v-else-if="activeTab === 'audit'"
        :isDark="isDark"
      />
    </main>

    <!-- Toast Notification -->
    <div
      v-if="toast"
      class="fixed bottom-5 right-5 z-50 max-w-md px-4 py-3 rounded-xl border shadow-xl text-xs font-medium backdrop-blur-md transition-all duration-300"
      :class="toast.type === 'error'
        ? 'bg-rose-900/90 border-rose-500/50 text-white'
        : 'bg-teal-900/90 border-teal-500/50 text-white'"
    >
      {{ toast.message }}
    </div>

    <!-- Hospital Footer -->
    <footer class="border-t py-4 text-center text-xs transition-colors duration-200 no-print"
            :class="isDark ? 'border-slate-800/80 bg-slate-900/40 text-slate-500' : 'border-slate-200 bg-white/70 text-slate-500'">
      <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div>
          © 2026 Bệnh viện Đa khoa MedShare · Hệ thống Hồ sơ Bệnh án Điện tử (EMR) &amp; PACS
        </div>
        <div class="text-[11px] text-slate-500 dark:text-slate-400">
          Tuân thủ Thông tư 46/2018/TT-BYT &amp; Nghị định 13/2023/NĐ-CP Bảo vệ Dữ liệu Cá nhân
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import axios from 'axios';
import LoginView from './components/LoginView.vue';
import Navbar from './components/Navbar.vue';
import AccountsTab from './components/AccountsTab.vue';
import PatientsTab from './components/PatientsTab.vue';
import AttachmentsTab from './components/AttachmentsTab.vue';
import CryptoTab from './components/CryptoTab.vue';
import DbaAuditTab from './components/DbaAuditTab.vue';
import AuditLogTab from './components/AuditLogTab.vue';

const checkingSession = ref(true);
const currentUser = ref(null);
const activeTab = ref('patients');
const loadingPatients = ref(false);
const patientsResponse = ref({ records: [], status: 'OK', message: '' });
const toast = ref(null);

// Theme State (Default to Light mode for authentic hospital EHR feel, or restore user preference)
const isDark = ref(localStorage.getItem('medshare_theme') === 'dark');

const applyTheme = (dark) => {
  if (dark) {
    document.documentElement.classList.add('dark');
    localStorage.setItem('medshare_theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    localStorage.setItem('medshare_theme', 'light');
  }
};

const toggleTheme = () => {
  isDark.value = !isDark.value;
  applyTheme(isDark.value);
};

const showToast = (payload) => {
  toast.value = payload;
  setTimeout(() => {
    if (toast.value === payload) toast.value = null;
  }, 4500);
};

const ALL_TABS = [
  { id: 'patients', label: 'Bệnh án Điện tử (EMR)', badge: 'Lâm sàng' },
  { id: 'attachments', label: 'Chẩn đoán Hình ảnh & PDF (PACS)', badge: 'PACS' },
  { id: 'crypto', label: 'Chia sẻ Liên viện & BFV', badge: 'Hội chẩn' },
  { id: 'accounts', label: 'Cấp thẻ & Tài khoản', badge: 'Quản trị' },
  { id: 'dba', label: 'Thanh tra Cloud DBMS', badge: 'DBA' },
  { id: 'audit', label: 'Sổ Nhật ký Lâm sàng', badge: 'Nhật ký' },
];

const visibleTabs = computed(() => {
  const role = (currentUser.value?.role || '').toUpperCase();
  if (role === 'ADMIN') {
    return ALL_TABS.filter((t) => ['accounts', 'audit', 'dba'].includes(t.id));
  }
  if (role === 'DBA') {
    return ALL_TABS.filter((t) => ['dba'].includes(t.id));
  }
  if (role === 'ANALYST' || role === 'RESEARCHER') {
    return ALL_TABS.filter((t) => ['crypto'].includes(t.id));
  }
  return ALL_TABS.filter((t) => ['patients', 'attachments', 'crypto'].includes(t.id));
});

const defaultTabForRole = (role) => {
  const upper = (role || '').toUpperCase();
  if (upper === 'ADMIN') return 'accounts';
  if (upper === 'DBA') return 'dba';
  if (upper === 'ANALYST' || upper === 'RESEARCHER') return 'crypto';
  return 'patients';
};

const loadPatients = async () => {
  if (!currentUser.value) return;
  loadingPatients.value = true;
  try {
    const { data } = await axios.get('/api/v1/patients', {
      params: { permitted_only: true },
    });
    patientsResponse.value = data;
  } catch (err) {
    console.error('Failed to fetch patients:', err);
    patientsResponse.value = {
      records: [],
      status: 'ERROR',
      message: err.response?.data?.detail || 'Lỗi tải dữ liệu hồ sơ',
    };
  } finally {
    loadingPatients.value = false;
  }
};

const clearSessionLocal = () => {
  localStorage.removeItem('medshare_jwt');
  localStorage.removeItem('medshare_user');
  delete axios.defaults.headers.common['Authorization'];
  currentUser.value = null;
  patientsResponse.value = { records: [], status: 'OK', message: '' };
};

const handleAuthenticated = async (authData) => {
  currentUser.value = authData.user;
  axios.defaults.headers.common['Authorization'] = `Bearer ${authData.access_token}`;
  activeTab.value = defaultTabForRole(authData.user.role);
  await loadPatients();
};

const handleLogout = async () => {
  try {
    if (localStorage.getItem('medshare_jwt')) {
      await axios.post('/api/v1/auth/logout');
    }
  } catch {
    // Ignore errors when token already expired/revoked
  } finally {
    clearSessionLocal();
  }
};

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const reqUrl = error.config?.url || '';
    if (error.response?.status === 401 && !reqUrl.includes('/api/v1/auth/login')) {
      clearSessionLocal();
    }
    return Promise.reject(error);
  }
);

watch(activeTab, (newTab) => {
  if (newTab === 'patients' && currentUser.value) {
    loadPatients();
  }
});

onMounted(async () => {
  applyTheme(isDark.value);
  const token = localStorage.getItem('medshare_jwt');
  if (!token) {
    checkingSession.value = false;
    return;
  }
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  try {
    const { data } = await axios.get('/api/v1/auth/me');
    currentUser.value = data.user;
    activeTab.value = defaultTabForRole(data.user.role);
    await loadPatients();
  } catch {
    clearSessionLocal();
  } finally {
    checkingSession.value = false;
  }
});
</script>
