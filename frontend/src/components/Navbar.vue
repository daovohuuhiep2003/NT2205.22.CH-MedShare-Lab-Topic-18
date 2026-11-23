<template>
  <header class="sticky top-0 z-30 border-b transition-colors duration-200 bg-white/95 dark:bg-slate-900/95 border-slate-200 dark:border-slate-800 backdrop-blur-md shadow-sm dark:shadow-none">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
      <!-- Hospital Brand & Facility Info -->
      <div class="flex items-center space-x-3.5">
        <!-- Hospital Medical Cross Logo -->
        <div class="relative flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-br from-teal-600 via-emerald-600 to-cyan-600 shadow-md shadow-teal-500/20 text-white flex-shrink-0">
          <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <!-- Medical Cross & Heartbeat -->
            <path d="M12 2v4m0 12v4M2 12h4m12 0h4" />
            <path d="M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
            <circle cx="12" cy="12" r="3" fill="currentColor" fill-opacity="0.3" />
          </svg>
          <span class="absolute -bottom-0.5 -right-0.5 flex h-3 w-3">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
        </div>

        <div>
          <div class="flex flex-wrap items-center gap-2">
            <h1 class="text-base sm:text-lg font-extrabold tracking-tight text-slate-900 dark:text-white flex items-center gap-1.5">
              <span>BỆNH VIỆN ĐA KHOA MEDSHARE</span>
            </h1>
            <span class="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-500/15 dark:text-teal-300 dark:border-teal-500/30 rounded-full">
              Hệ thống Bệnh án Điện tử (EMR / PACS)
            </span>
          </div>
          <div class="flex flex-wrap items-center gap-x-2 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            <span class="font-medium text-teal-700 dark:text-teal-400">Cơ sở A: 120 Hai Bà Trưng, Q.1</span>
            <span>·</span>
            <span>Liên thông BHYT &amp; Bộ Y tế</span>
            <span class="hidden sm:inline">·</span>
            <span class="hidden sm:inline text-[11px] text-teal-700 dark:text-teal-400 font-semibold">Cổng Dịch vụ Y tế Trực tuyến</span>
          </div>
        </div>
      </div>

      <!-- Authenticated Identity Controls & Theme Switcher -->
      <div v-if="user" class="flex flex-wrap items-center gap-2 sm:gap-2.5">
        <!-- Duty Station & Personnel Badge -->
        <div class="flex items-center space-x-2.5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-xs">
          <div class="w-8 h-8 rounded-lg bg-teal-100 text-teal-800 dark:bg-teal-900/60 dark:text-teal-200 flex items-center justify-center font-bold text-xs flex-shrink-0">
            {{ userInitials }}
          </div>
          <div class="flex flex-col text-left">
            <div class="flex items-center space-x-1.5">
              <span class="text-xs font-bold text-slate-900 dark:text-slate-100 truncate max-w-[140px] sm:max-w-none">
                {{ user.full_name }}
              </span>
              <span :class="roleBadgeClass" class="px-1.5 py-0.5 text-[10px] font-bold rounded border uppercase">
                {{ user.role }}
              </span>
            </div>
            <div class="flex items-center space-x-1.5 text-[10px] text-slate-500 dark:text-slate-400 font-mono">
              <span class="text-teal-700 dark:text-teal-300 font-semibold">{{ user.department }}</span>
              <span>·</span>
              <span>@{{ user.username }}</span>
              <span v-if="user.patient_id" class="text-amber-600 dark:text-amber-400 font-bold">· {{ user.patient_id }}</span>
            </div>
          </div>
        </div>

        <!-- Light / Dark Mode Toggle Button -->
        <button
          type="button"
          @click="$emit('toggle-theme')"
          class="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl border transition shadow-xs"
          :class="isDark
            ? 'bg-slate-800 hover:bg-slate-700 text-amber-300 border-slate-700'
            : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-200'"
          :title="isDark ? 'Chuyển sang Giao diện Sáng (Ban ngày / Phòng khám)' : 'Chuyển sang Giao diện Tối (Ban đêm / Trực viện)'"
        >
          <span v-if="isDark" class="text-sm">☀️</span>
          <span v-else class="text-sm">🌙</span>
          <span class="hidden sm:inline">{{ isDark ? 'Giao diện Sáng' : 'Giao diện Tối' }}</span>
        </button>

        <!-- Change Password Button -->
        <button
          @click="showPwModal = true"
          class="px-2.5 py-1.5 text-xs font-semibold rounded-xl border transition bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700"
          title="Đổi mật khẩu tài khoản hiện tại"
        >
          Đổi mật khẩu
        </button>

        <!-- Logout Button -->
        <button
          @click="$emit('logout')"
          class="px-3 py-1.5 text-xs font-semibold rounded-xl border transition bg-rose-50 hover:bg-rose-100 text-rose-700 border-rose-200 dark:bg-rose-500/10 dark:hover:bg-rose-500/20 dark:text-rose-300 dark:border-rose-500/30"
        >
          Đăng xuất
        </button>
      </div>
    </div>

    <!-- Change Password Modal -->
    <div
      v-if="showPwModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 dark:bg-black/75 backdrop-blur-sm p-4"
    >
      <div class="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-2xl">
        <div class="flex items-center justify-between mb-4 pb-3 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white">Đổi mật khẩu tài khoản (@{{ user?.username }})</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Mật khẩu được mã hóa an toàn bằng Argon2id tại Zone Z1</p>
          </div>
          <button @click="closePwModal" class="text-slate-400 hover:text-slate-600 dark:hover:text-white text-base">✕</button>
        </div>

        <form @submit.prevent="submitPasswordChange" class="space-y-3.5 text-xs">
          <div>
            <label class="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Mật khẩu hiện tại *</label>
            <input
              v-model="pwForm.old_password"
              type="password"
              required
              class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-lg px-3 py-2 text-slate-900 dark:text-slate-100 focus:border-teal-500 focus:outline-none"
            />
          </div>
          <div>
            <label class="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Mật khẩu mới (>= 8 ký tự) *</label>
            <input
              v-model="pwForm.new_password"
              type="password"
              minlength="8"
              required
              class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-lg px-3 py-2 text-slate-900 dark:text-slate-100 focus:border-teal-500 focus:outline-none"
            />
          </div>

          <div v-if="pwError" class="p-2.5 rounded-lg bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-500/10 dark:border-rose-500/30 dark:text-rose-300">
            {{ pwError }}
          </div>

          <div class="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              @click="closePwModal"
              class="px-3.5 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300"
            >
              Hủy
            </button>
            <button
              type="submit"
              :disabled="pwLoading"
              class="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold transition shadow-sm"
            >
              {{ pwLoading ? 'Đang cập nhật...' : 'Cập nhật & Đăng nhập lại' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import axios from 'axios';

const props = defineProps({
  user: {
    type: Object,
    default: null,
  },
  isDark: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['logout', 'password-changed', 'toggle-theme']);

const showPwModal = ref(false);
const pwLoading = ref(false);
const pwError = ref('');
const pwForm = reactive({
  old_password: '',
  new_password: '',
});

const userInitials = computed(() => {
  if (!props.user?.full_name) return 'BN';
  const parts = props.user.full_name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
});

const roleBadgeClass = computed(() => {
  const role = (props.user?.role || '').toUpperCase();
  if (role === 'DOCTOR') {
    return 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-500/15 dark:text-blue-300 dark:border-blue-500/30';
  }
  if (role === 'NURSE') {
    return 'bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-500/15 dark:text-cyan-300 dark:border-cyan-500/30';
  }
  if (role === 'PATIENT' || role === 'PATIENT_FAMILY') {
    return 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30';
  }
  if (role === 'ADMIN') {
    return 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-500/15 dark:text-purple-300 dark:border-purple-500/30';
  }
  if (role === 'DBA') {
    return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30';
  }
  return 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
});

const closePwModal = () => {
  showPwModal.value = false;
  pwError.value = '';
  pwForm.old_password = '';
  pwForm.new_password = '';
};

const submitPasswordChange = async () => {
  pwError.value = '';
  pwLoading.value = true;
  try {
    await axios.post('/api/v1/auth/change-password', {
      old_password: pwForm.old_password,
      new_password: pwForm.new_password,
    });
    closePwModal();
    emit('password-changed');
  } catch (err) {
    pwError.value = err.response?.data?.detail || 'Không thể đổi mật khẩu.';
  } finally {
    pwLoading.value = false;
  }
};
</script>
