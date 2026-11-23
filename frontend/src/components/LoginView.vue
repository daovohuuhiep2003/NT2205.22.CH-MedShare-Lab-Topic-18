<template>
  <div class="min-h-screen flex flex-col justify-center items-center p-4 transition-colors duration-200"
       :class="isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-100/90 text-slate-800'">
    
    <!-- Top Bar with Hospital Brand and Theme Switcher -->
    <div class="w-full max-w-4xl flex items-center justify-between mb-4 px-2">
      <div class="flex items-center space-x-2.5">
        <div class="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-bold shadow-md">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
          </svg>
        </div>
        <div>
          <span class="text-xs font-black tracking-wider uppercase text-teal-800 dark:text-teal-400">
            BỆNH VIỆN ĐA KHOA QUỐC TẾ MEDSHARE
          </span>
          <span class="hidden sm:inline text-xs text-slate-500 dark:text-slate-400 font-medium ml-2">
            · Cổng Bệnh án Điện tử (EMR) &amp; PACS
          </span>
        </div>
      </div>

      <!-- Theme Switcher Button -->
      <button
        @click="$emit('toggle-theme')"
        type="button"
        class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition shadow-xs"
        :class="isDark
          ? 'bg-slate-900 border-slate-700 text-amber-300 hover:bg-slate-850'
          : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-teal-700'"
        :title="isDark ? 'Chuyển sang Chế độ Sáng' : 'Chuyển sang Chế độ Tối'"
      >
        <span v-if="isDark" class="flex items-center space-x-1">
          <span>☀️</span>
          <span class="font-sans">Chế độ Sáng</span>
        </span>
        <span v-else class="flex items-center space-x-1">
          <span>🌙</span>
          <span class="font-sans">Chế độ Tối</span>
        </span>
      </button>
    </div>

    <!-- Login Container Card -->
    <div class="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-5 border rounded-2xl overflow-hidden shadow-2xl transition-colors duration-200"
         :class="isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'">
      
      <!-- Left Hospital Information & Regulatory Notices -->
      <div class="lg:col-span-2 p-6 sm:p-8 border-b lg:border-b-0 lg:border-r flex flex-col justify-between transition-colors"
           :class="isDark
             ? 'bg-gradient-to-br from-slate-900 via-slate-900 to-teal-950/40 border-slate-800 text-slate-300'
             : 'bg-gradient-to-br from-teal-50/70 via-slate-50 to-emerald-50/40 border-slate-200 text-slate-700'">
        <div>
          <div class="flex items-center space-x-3 mb-5">
            <div class="flex items-center justify-center w-11 h-11 rounded-xl bg-teal-600 text-white shadow-lg shadow-teal-600/30">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h1 class="text-base font-bold text-slate-900 dark:text-white leading-tight">MedShare EHR / PACS</h1>
              <p class="text-[11px] font-semibold text-teal-700 dark:text-teal-400">Hệ thống Hồ sơ Y tế Điện tử</p>
            </div>
          </div>

          <h2 class="text-lg font-bold text-slate-900 dark:text-white mb-2">Cổng Quản lý Bệnh án</h2>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed mb-5">
            Hệ thống hỗ trợ y bác sĩ, điều dưỡng theo dõi quá trình điều trị người bệnh, tra cứu hồ sơ và đọc kết quả chẩn đoán hình ảnh PACS.
          </p>

          <div class="space-y-3.5 text-xs">
            <div class="flex items-start space-x-2.5">
              <span class="text-teal-600 dark:text-teal-400 font-bold text-sm">📋</span>
              <div>
                <strong class="text-slate-900 dark:text-slate-200">Hồ sơ Bệnh án Điện tử:</strong>
                <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Quản lý toàn diện bệnh án nội trú, ngoại trú, theo dõi sinh hiệu và diễn biến bệnh hàng ngày.</p>
              </div>
            </div>
            <div class="flex items-start space-x-2.5">
              <span class="text-teal-600 dark:text-teal-400 font-bold text-sm">🩺</span>
              <div>
                <strong class="text-slate-900 dark:text-slate-200">Phân quyền Theo Chuyên khoa:</strong>
                <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Cán bộ y tế được phân quyền quản lý ca bệnh thuộc chuyên khoa phụ trách theo quy chế bệnh viện.</p>
              </div>
            </div>
            <div class="flex items-start space-x-2.5">
              <span class="text-teal-600 dark:text-teal-400 font-bold text-sm">🔒</span>
              <div>
                <strong class="text-slate-900 dark:text-slate-200">Bảo mật Thông tin Người bệnh:</strong>
                <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Tuân thủ tiêu chuẩn Bệnh án Điện tử Thông tư 46/2018/TT-BYT và Luật Khám bệnh, chữa bệnh.</p>
              </div>
            </div>
            <div class="flex items-start space-x-2.5">
              <span class="text-teal-600 dark:text-teal-400 font-bold text-sm">📞</span>
              <div>
                <strong class="text-slate-900 dark:text-slate-200">Hỗ trợ Kỹ thuật &amp; Tài khoản:</strong>
                <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Phòng Công nghệ Thông tin Bệnh viện · Tổng đài nội bộ: 108.</p>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6 pt-4 border-t text-[11px]"
             :class="isDark ? 'border-slate-800 text-slate-400' : 'border-slate-200 text-slate-500'">
          <span>Hệ thống dành riêng cho Cán bộ Y tế và Người bệnh đã được cấp quyền truy cập.</span>
        </div>
      </div>

      <!-- Right Login Form -->
      <div class="lg:col-span-3 p-6 sm:p-10 flex flex-col justify-center">
        <form @submit.prevent="submitLogin" class="space-y-4 max-w-md w-full mx-auto">
          <div>
            <h3 class="text-lg font-bold text-slate-900 dark:text-white">Đăng nhập Hệ thống</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Vui lòng nhập tài khoản và mật khẩu được cấp.</p>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5" for="login-username">
              Tên đăng nhập (Username)
            </label>
            <input
              id="login-username"
              v-model.trim="username"
              type="text"
              autocomplete="username"
              required
              placeholder="Nhập tên đăng nhập"
              class="w-full rounded-xl px-3.5 py-2.5 text-sm border transition focus:outline-none focus:ring-2 focus:ring-teal-500/50"
              :class="isDark
                ? 'bg-slate-950 border-slate-700 text-white placeholder-slate-500 focus:border-teal-500'
                : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:bg-white focus:border-teal-600'"
            />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300" for="login-password">
                Mật khẩu
              </label>
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="text-[11px] text-teal-700 dark:text-teal-400 hover:underline"
              >
                {{ showPassword ? '🙈 Ẩn mật khẩu' : '👁 Hiện mật khẩu' }}
              </button>
            </div>
            <div class="relative">
              <input
                id="login-password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
                placeholder="Nhập mật khẩu"
                class="w-full rounded-xl px-3.5 py-2.5 text-sm border font-mono transition focus:outline-none focus:ring-2 focus:ring-teal-500/50"
                :class="isDark
                  ? 'bg-slate-950 border-slate-700 text-white placeholder-slate-500 focus:border-teal-500'
                  : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:bg-white focus:border-teal-600'"
              />
            </div>
          </div>

          <div
            v-if="errorMsg"
            class="p-3 rounded-xl bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs"
          >
            {{ errorMsg }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 px-4 rounded-xl font-bold text-sm transition shadow-md"
            :class="isDark
              ? 'bg-teal-500 hover:bg-teal-400 text-slate-950 disabled:opacity-60 shadow-teal-500/20'
              : 'bg-teal-600 hover:bg-teal-700 text-white disabled:opacity-60 shadow-teal-600/20'"
          >
            {{ loading ? 'Đang đăng nhập...' : 'Đăng nhập vào Hệ thống' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['authenticated', 'toggle-theme']);

const username = ref('');
const password = ref('');
const showPassword = ref(false);
const loading = ref(false);
const errorMsg = ref('');

const submitLogin = async () => {
  errorMsg.value = '';
  loading.value = true;
  try {
    const { data } = await axios.post('/api/v1/auth/login', {
      username: username.value,
      password: password.value,
    });
    localStorage.setItem('medshare_jwt', data.access_token);
    localStorage.setItem('medshare_user', JSON.stringify(data.user));
    axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
    password.value = '';
    emit('authenticated', data);
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Đăng nhập thất bại. Vui lòng kiểm tra lại tên đăng nhập hoặc mật khẩu.';
  } finally {
    loading.value = false;
  }
};
</script>
