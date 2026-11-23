<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-5 rounded-2xl border transition-colors shadow-xs"
         :class="isDark ? 'bg-slate-900/60 border-slate-800' : 'bg-white border-slate-200'">
      <div>
        <h2 class="text-lg font-bold flex items-center space-x-2"
            :class="isDark ? 'text-white' : 'text-slate-900'">
          <span>Quản lý &amp; Cấp phát Tài khoản (Zone Z1 IdP)</span>
          <span class="px-2 py-0.5 text-xs rounded font-mono font-semibold"
                :class="isDark ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20' : 'bg-teal-50 text-teal-800 border border-teal-200'">
            Argon2id + HMAC-SHA-256
          </span>
        </h2>
        <p class="text-xs mt-1" :class="isDark ? 'text-slate-400' : 'text-slate-600'">
          Cấp tài khoản đăng nhập cá thể hóa cho từng bên liên quan, map 1:1 với dữ liệu hồ sơ bệnh nhân trong DB, kiểm tra tính toàn vẹn thuộc tính và thu hồi quyền tức thời (TC-07).
        </p>
      </div>

      <button
        @click="loadAccounts"
        :disabled="loading"
        class="px-3.5 py-2 text-xs font-semibold rounded-xl border transition self-start sm:self-auto shadow-xs"
        :class="isDark
          ? 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700'
          : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'"
      >
        {{ loading ? 'Đang tải...' : '↻ Tải lại danh sách' }}
      </button>
    </div>

    <!-- Mapping Statistics 1:1 Banner -->
    <div v-if="stats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="p-4 rounded-2xl border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/70 border-slate-800' : 'bg-white border-slate-200'">
        <div class="text-[11px] font-medium" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Hồ sơ Bệnh nhân trong DB</div>
        <div class="text-2xl font-black font-mono mt-1 text-cyan-600 dark:text-cyan-400">
          {{ stats.total_patient_records_in_db?.toLocaleString('vi-VN') || 0 }}
        </div>
        <div class="text-[10px] mt-1 text-slate-500">1.000 hồ sơ EHR (hosp-a + b)</div>
      </div>

      <div class="p-4 rounded-2xl border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/70 border-slate-800' : 'bg-white border-slate-200'">
        <div class="text-[11px] font-medium" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Tài khoản Bệnh nhân (PATIENT)</div>
        <div class="text-2xl font-black font-mono mt-1 text-teal-600 dark:text-teal-400">
          {{ stats.patient_accounts_count?.toLocaleString('vi-VN') || 0 }}
        </div>
        <div class="text-[10px] mt-1 text-slate-500">Tên cá thể hóa (vd: hailt001)</div>
      </div>

      <div class="p-4 rounded-2xl border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/70 border-slate-800' : 'bg-white border-slate-200'">
        <div class="text-[11px] font-medium" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Khớp nối 1:1 Hồ sơ - Tài khoản</div>
        <div class="text-2xl font-black font-mono mt-1 flex items-center space-x-1.5"
             :class="stats.one_to_one_mapped ? 'text-teal-600 dark:text-teal-400' : 'text-amber-600 dark:text-amber-400'">
          <span>{{ ((stats.mapping_ratio || 0) * 100).toFixed(0) }}%</span>
          <span v-if="stats.one_to_one_mapped" class="text-xs font-bold px-1.5 py-0.5 rounded"
                :class="isDark ? 'bg-teal-500/20 text-teal-300' : 'bg-teal-100 text-teal-800'">1:1 Đạt</span>
        </div>
        <div class="text-[10px] mt-1 text-slate-500">
          Chưa map: {{ stats.unmapped_records_count || 0 }} hồ sơ
        </div>
      </div>

      <div class="p-4 rounded-2xl border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/70 border-slate-800' : 'bg-white border-slate-200'">
        <div class="text-[11px] font-medium" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Cán bộ Y tế &amp; Quản trị</div>
        <div class="text-2xl font-black font-mono mt-1 text-purple-600 dark:text-purple-400">
          {{ ((stats.total_accounts || 0) - (stats.patient_accounts_count || 0)).toLocaleString('vi-VN') }}
        </div>
        <div class="text-[10px] mt-1 text-slate-500">Bác sĩ, ĐD, DBA, Analyst, Admin</div>
      </div>
    </div>

    <!-- Non-Admin 403 block -->
    <div
      v-if="forbiddenError"
      class="p-5 rounded-2xl border text-sm"
      :class="isDark ? 'bg-rose-500/10 border-rose-500/30 text-rose-200' : 'bg-rose-50 border-rose-200 text-rose-800'"
    >
      <p class="font-bold text-rose-600 dark:text-rose-400 mb-1">Truy cập bị từ chối (403 Forbidden)</p>
      <p class="text-xs">{{ forbiddenError }}</p>
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Provisioning Form -->
      <div class="lg:col-span-1 rounded-2xl p-5 border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/60 border-slate-800' : 'bg-white border-slate-200'">
        <h3 class="text-sm font-bold mb-1" :class="isDark ? 'text-white' : 'text-slate-900'">Cấp phát Tài khoản Mới</h3>
        <p class="text-[11px] mb-4" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
          Quản trị viên Zone Z1 khởi tạo danh tính và gắn nhãn bảo vệ HMAC-SHA-256 cho người dùng mới.
        </p>

        <form @submit.prevent="createAccount" class="space-y-3.5 text-xs">
          <div>
            <label class="block font-semibold mb-1" :class="isDark ? 'text-slate-300' : 'text-slate-700'">Tên đăng nhập (username) *</label>
            <input
              v-model.trim="form.username"
              required
              minlength="3"
              maxlength="32"
              placeholder="vd: dr_linh_cardio"
              class="w-full rounded-xl px-3 py-2 border transition focus:outline-none focus:ring-2 focus:ring-teal-500/50"
              :class="isDark
                ? 'bg-slate-950 border-slate-700 text-slate-100 placeholder-slate-500 focus:border-teal-500'
                : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:bg-white focus:border-teal-600'"
            />
          </div>

          <div>
            <label class="block font-semibold mb-1" :class="isDark ? 'text-slate-300' : 'text-slate-700'">Mật khẩu ban đầu (>= 8 ký tự) *</label>
            <input
              v-model="form.password"
              type="password"
              required
              minlength="8"
              placeholder="Nhập mật khẩu khởi tạo"
              class="w-full rounded-xl px-3 py-2 border transition focus:outline-none focus:ring-2 focus:ring-teal-500/50"
              :class="isDark
                ? 'bg-slate-950 border-slate-700 text-slate-100 placeholder-slate-500 focus:border-teal-500'
                : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:bg-white focus:border-teal-600'"
            />
          </div>

          <div>
            <label class="block font-semibold mb-1" :class="isDark ? 'text-slate-300' : 'text-slate-700'">Họ tên / Tên tổ chức *</label>
            <input
              v-model.trim="form.full_name"
              required
              placeholder="vd: BS. Nguyễn Khánh Linh"
              class="w-full rounded-xl px-3 py-2 border transition focus:outline-none focus:ring-2 focus:ring-teal-500/50"
              :class="isDark
                ? 'bg-slate-950 border-slate-700 text-slate-100 placeholder-slate-500 focus:border-teal-500'
                : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:bg-white focus:border-teal-600'"
            />
          </div>

          <div class="grid grid-cols-2 gap-2.5">
            <div>
              <label class="block font-semibold mb-1" :class="isDark ? 'text-slate-300' : 'text-slate-700'">Vai trò (Role) *</label>
              <select
                v-model="form.role"
                @change="onRoleChange"
                class="w-full rounded-xl px-2.5 py-2 border transition focus:outline-none focus:ring-2 focus:ring-teal-500/50"
                :class="isDark
                  ? 'bg-slate-950 border-slate-700 text-slate-100 focus:border-teal-500'
                  : 'bg-slate-50 border-slate-300 text-slate-900 focus:bg-white focus:border-teal-600'"
              >
                <option value="DOCTOR">DOCTOR</option>
                <option value="NURSE">NURSE</option>
                <option value="PATIENT">PATIENT</option>
                <option value="PATIENT_FAMILY">PATIENT_FAMILY</option>
                <option value="ANALYST">ANALYST</option>
                <option value="RESEARCHER">RESEARCHER</option>
                <option value="DBA">DBA</option>
                <option value="ADMIN">ADMIN</option>
              </select>
            </div>

            <div>
              <label class="block font-semibold mb-1" :class="isDark ? 'text-slate-300' : 'text-slate-700'">Khoa / Đơn vị *</label>
              <input
                v-model.trim="form.department"
                list="dept-options"
                required
                placeholder="CARDIOLOGY"
                class="w-full rounded-xl px-2.5 py-2 border transition focus:outline-none focus:ring-2 focus:ring-teal-500/50"
                :class="isDark
                  ? 'bg-slate-950 border-slate-700 text-slate-100 focus:border-teal-500'
                  : 'bg-slate-50 border-slate-300 text-slate-900 focus:bg-white focus:border-teal-600'"
              />
              <datalist id="dept-options">
                <option value="CARDIOLOGY" />
                <option value="ONCOLOGY" />
                <option value="PEDIATRICS" />
                <option value="NEUROLOGY" />
                <option value="GENERAL" />
                <option value="PATIENT_PORTAL" />
                <option value="RESEARCH" />
                <option value="SECURITY" />
                <option value="INFRASTRUCTURE" />
              </datalist>
            </div>
          </div>

          <div v-if="needsPatientId">
            <label class="block font-semibold mb-1" :class="isDark ? 'text-amber-400' : 'text-amber-700'">Mã hồ sơ bệnh nhân liên kết (record_id) *</label>
            <input
              v-model.trim="form.patient_id"
              required
              placeholder="vd: rec-pat-001"
              class="w-full rounded-xl px-3 py-2 border transition focus:outline-none focus:ring-2 focus:ring-amber-500/50"
              :class="isDark
                ? 'bg-slate-950 border-amber-500/40 text-slate-100 focus:border-amber-400'
                : 'bg-amber-50/50 border-amber-300 text-slate-900 focus:bg-white focus:border-amber-600'"
            />
          </div>

          <div class="grid grid-cols-2 gap-2.5">
            <div>
              <label class="block font-semibold mb-1" :class="isDark ? 'text-slate-300' : 'text-slate-700'">Cơ sở (Tenant)</label>
              <input
                v-model.trim="form.tenant_id"
                class="w-full rounded-xl px-2.5 py-2 border transition focus:outline-none focus:ring-2 focus:ring-teal-500/50"
                :class="isDark
                  ? 'bg-slate-950 border-slate-700 text-slate-100 focus:border-teal-500'
                  : 'bg-slate-50 border-slate-300 text-slate-900 focus:bg-white focus:border-teal-600'"
              />
            </div>
            <div>
              <label class="block font-semibold mb-1" :class="isDark ? 'text-slate-300' : 'text-slate-700'">Chức danh / Mô tả</label>
              <input
                v-model.trim="form.title"
                placeholder="Tùy chọn"
                class="w-full rounded-xl px-2.5 py-2 border transition focus:outline-none focus:ring-2 focus:ring-teal-500/50"
                :class="isDark
                  ? 'bg-slate-950 border-slate-700 text-slate-100 focus:border-teal-500'
                  : 'bg-slate-50 border-slate-300 text-slate-900 focus:bg-white focus:border-teal-600'"
              />
            </div>
          </div>

          <div v-if="formError" class="p-3 rounded-xl border text-xs"
               :class="isDark ? 'bg-rose-500/10 border-rose-500/30 text-rose-300' : 'bg-rose-50 border-rose-200 text-rose-700'">
            {{ formError }}
          </div>
          <div v-if="formSuccess" class="p-3 rounded-xl border text-xs"
               :class="isDark ? 'bg-teal-500/10 border-teal-500/30 text-teal-300' : 'bg-teal-50 border-teal-200 text-teal-800'">
            {{ formSuccess }}
          </div>

          <button
            type="submit"
            :disabled="submitting"
            class="w-full py-2.5 rounded-xl font-bold transition shadow-md"
            :class="isDark
              ? 'bg-teal-500 hover:bg-teal-400 disabled:opacity-60 text-slate-950 shadow-teal-500/20'
              : 'bg-teal-600 hover:bg-teal-700 disabled:opacity-60 text-white shadow-teal-600/20'"
          >
            {{ submitting ? 'Đang tạo & ký HMAC Z1...' : '+ Cấp tài khoản' }}
          </button>
        </form>
      </div>

      <!-- Accounts Table & Filters -->
      <div class="lg:col-span-2 space-y-3">
        <!-- Filter and Search Bar -->
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 rounded-2xl border transition-colors shadow-xs"
             :class="isDark ? 'bg-slate-900/60 border-slate-800' : 'bg-white border-slate-200'">
          <div class="flex-1 flex items-center space-x-2">
            <input
              v-model="searchQuery"
              @keyup.enter="applyFilter"
              placeholder="Tìm theo username, họ tên, mã hồ sơ..."
              class="w-full rounded-xl px-3 py-2 text-xs border transition focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
              :class="isDark
                ? 'bg-slate-950 border-slate-700 text-slate-100 placeholder-slate-500 focus:border-cyan-500'
                : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:bg-white focus:border-cyan-600'"
            />
            <button
              @click="applyFilter"
              class="px-3.5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-semibold transition shadow-xs"
            >
              Tìm
            </button>
          </div>

          <div class="flex items-center space-x-2">
            <select
              v-model="selectedRole"
              @change="applyFilter"
              class="rounded-xl px-2.5 py-2 text-xs border transition focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
              :class="isDark
                ? 'bg-slate-950 border-slate-700 text-slate-200 focus:border-cyan-500'
                : 'bg-slate-50 border-slate-300 text-slate-800 focus:bg-white focus:border-cyan-600'"
            >
              <option value="">Tất cả vai trò</option>
              <option value="PATIENT">PATIENT (Bệnh nhân)</option>
              <option value="DOCTOR">DOCTOR (Bác sĩ)</option>
              <option value="NURSE">NURSE (Điều dưỡng)</option>
              <option value="PATIENT_FAMILY">PATIENT_FAMILY (Người nhà)</option>
              <option value="ANALYST">ANALYST (Phân tích)</option>
              <option value="DBA">DBA (Quản trị CSDL)</option>
              <option value="ADMIN">ADMIN (Quản trị Z1)</option>
            </select>

            <button
              v-if="selectedRole || searchQuery"
              @click="resetFilter"
              class="px-2.5 py-2 text-xs rounded-xl border transition shadow-xs"
              :class="isDark
                ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'"
              title="Đặt lại bộ lọc"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Accounts Table -->
        <div class="overflow-x-auto rounded-2xl border transition-colors shadow-xs"
             :class="isDark ? 'border-slate-800 bg-slate-900/40' : 'border-slate-200 bg-white'">
          <table class="w-full text-left border-collapse text-xs">
            <thead>
              <tr class="border-b text-[11px] font-semibold uppercase"
                  :class="isDark ? 'border-slate-800 bg-slate-800/50 text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-600'">
                <th class="py-3 px-4">Tài khoản</th>
                <th class="py-3 px-4">Vai trò / Khoa</th>
                <th class="py-3 px-4">Z1 HMAC</th>
                <th class="py-3 px-4">Trạng thái</th>
                <th class="py-3 px-4 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody class="divide-y"
                   :class="isDark ? 'divide-slate-800/60' : 'divide-slate-200'">
              <tr v-if="accounts.length === 0">
                <td colspan="5" class="py-8 text-center italic" :class="isDark ? 'text-slate-500' : 'text-slate-400'">
                  Không tìm thấy tài khoản phù hợp với điều kiện lọc.
                </td>
              </tr>
              <tr v-for="acc in accounts" :key="acc.username"
                  class="transition"
                  :class="isDark ? 'hover:bg-slate-800/30' : 'hover:bg-slate-50'">
                <td class="py-3 px-4">
                  <div class="font-bold font-mono" :class="isDark ? 'text-slate-100' : 'text-slate-900'">{{ acc.username }}</div>
                  <div class="text-[11px]" :class="isDark ? 'text-slate-300' : 'text-slate-700'">{{ acc.full_name }}</div>
                  <div class="text-[10px] font-mono text-slate-400">{{ acc.user_id }} · epoch {{ acc.attr_epoch }}</div>
                </td>
                <td class="py-3 px-4">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                        :class="isDark ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20' : 'bg-cyan-50 text-cyan-800 border border-cyan-200'">
                    {{ acc.role }}
                  </span>
                  <div class="text-[11px] mt-1 font-mono" :class="isDark ? 'text-slate-400' : 'text-slate-600'">{{ acc.department }}</div>
                  <div v-if="acc.patient_id" class="text-[10px] font-mono" :class="isDark ? 'text-amber-400' : 'text-amber-700'">
                    Hồ sơ: {{ acc.patient_id }}
                  </div>
                </td>
                <td class="py-3 px-4">
                  <span
                    v-if="acc.integrity_ok"
                    class="inline-flex px-2 py-0.5 rounded text-[10px] font-semibold"
                    :class="isDark ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20' : 'bg-teal-50 text-teal-800 border border-teal-200'"
                  >
                    ✓ HMAC Valid
                  </span>
                  <span
                    v-else
                    class="inline-flex px-2 py-0.5 rounded text-[10px] font-semibold"
                    :class="isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-rose-100 text-rose-800 border border-rose-200'"
                  >
                    ⚠ TAMPERED
                  </span>
                </td>
                <td class="py-3 px-4">
                  <span
                    v-if="acc.active"
                    class="inline-flex px-2 py-0.5 rounded text-[10px] font-semibold"
                    :class="isDark ? 'bg-teal-500/10 text-teal-400' : 'bg-teal-100 text-teal-800'"
                  >
                    ● Hoạt động
                  </span>
                  <span
                    v-else
                    class="inline-flex px-2 py-0.5 rounded text-[10px] font-semibold"
                    :class="isDark ? 'bg-rose-500/10 text-rose-400' : 'bg-rose-100 text-rose-800'"
                  >
                    ✕ Thu hồi (TC-07)
                  </span>
                </td>
                <td class="py-3 px-4 text-right">
                  <span v-if="acc.username === currentUsername" class="text-[10px] italic text-slate-400">
                    (Đang đăng nhập)
                  </span>
                  <button
                    v-else-if="acc.active"
                    @click="toggleStatus(acc.username, 'revoke')"
                    class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition"
                    :class="isDark
                      ? 'bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border-rose-500/30'
                      : 'bg-rose-50 hover:bg-rose-100 text-rose-700 border-rose-200'"
                  >
                    Thu hồi
                  </button>
                  <button
                    v-else
                    @click="toggleStatus(acc.username, 'restore')"
                    class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition"
                    :class="isDark
                      ? 'bg-teal-500/15 hover:bg-teal-500/25 text-teal-300 border-teal-500/30'
                      : 'bg-teal-50 hover:bg-teal-100 text-teal-800 border-teal-200'"
                  >
                    Khôi phục
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination Controls -->
        <div class="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs px-2 py-1"
             :class="isDark ? 'text-slate-400' : 'text-slate-600'">
          <div>
            Hiển thị <span class="font-semibold" :class="isDark ? 'text-slate-200' : 'text-slate-900'">{{ accounts.length }}</span> /
            <span class="font-semibold" :class="isDark ? 'text-slate-200' : 'text-slate-900'">{{ total.toLocaleString('vi-VN') }}</span> tài khoản
            (Trang {{ page }} / {{ totalPages }})
          </div>

          <div class="flex items-center space-x-2">
            <button
              @click="goToPage(page - 1)"
              :disabled="page <= 1 || loading"
              class="px-3 py-1.5 rounded-xl border transition disabled:opacity-40 disabled:cursor-not-allowed shadow-xs"
              :class="isDark
                ? 'border-slate-700 bg-slate-850 hover:bg-slate-750 text-slate-200'
                : 'border-slate-300 bg-white hover:bg-slate-50 text-slate-700'"
            >
              ← Trước
            </button>

            <span class="px-2 font-mono font-bold" :class="isDark ? 'text-cyan-400' : 'text-cyan-700'">{{ page }}</span>

            <button
              @click="goToPage(page + 1)"
              :disabled="page >= totalPages || loading"
              class="px-3 py-1.5 rounded-xl border transition disabled:opacity-40 disabled:cursor-not-allowed shadow-xs"
              :class="isDark
                ? 'border-slate-700 bg-slate-850 hover:bg-slate-750 text-slate-200'
                : 'border-slate-300 bg-white hover:bg-slate-50 text-slate-700'"
            >
              Sau →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import axios from 'axios';

const props = defineProps({
  currentUsername: {
    type: String,
    default: '',
  },
  isDark: {
    type: Boolean,
    default: false,
  },
});

const accounts = ref([]);
const loading = ref(false);
const submitting = ref(false);
const forbiddenError = ref('');
const formError = ref('');
const formSuccess = ref('');

const stats = ref(null);
const page = ref(1);
const pageSize = ref(25);
const total = ref(0);
const totalPages = ref(1);
const selectedRole = ref('');
const searchQuery = ref('');

const form = reactive({
  username: '',
  password: '',
  full_name: '',
  role: 'DOCTOR',
  department: 'CARDIOLOGY',
  tenant_id: 'hospital-a',
  patient_id: '',
  title: '',
});

const needsPatientId = computed(() =>
  form.role === 'PATIENT' || form.role === 'PATIENT_FAMILY'
);

const onRoleChange = () => {
  if (needsPatientId.value && (!form.department || form.department === 'CARDIOLOGY')) {
    form.department = 'PATIENT_PORTAL';
  }
};

const loadAccounts = async (targetPage = page.value) => {
  loading.value = true;
  forbiddenError.value = '';
  try {
    const params = {
      page: targetPage,
      page_size: pageSize.value,
    };
    if (selectedRole.value && selectedRole.value !== 'ALL') {
      params.role = selectedRole.value;
    }
    if (searchQuery.value && searchQuery.value.trim()) {
      params.search = searchQuery.value.trim();
    }
    const { data } = await axios.get('/api/v1/auth/accounts', { params });
    accounts.value = data.accounts || [];
    page.value = data.page || 1;
    pageSize.value = data.page_size || 25;
    total.value = data.total || 0;
    totalPages.value = data.total_pages || 1;
    if (data.stats) {
      stats.value = data.stats;
    }
  } catch (err) {
    if (err.response?.status === 403) {
      forbiddenError.value = err.response.data?.detail || 'Chỉ Quản trị viên (ADMIN) mới được truy cập chức năng này.';
    } else {
      forbiddenError.value = err.response?.data?.detail || 'Không thể tải danh sách tài khoản.';
    }
  } finally {
    loading.value = false;
  }
};

const applyFilter = () => {
  page.value = 1;
  loadAccounts(1);
};

const resetFilter = () => {
  selectedRole.value = '';
  searchQuery.value = '';
  page.value = 1;
  loadAccounts(1);
};

const goToPage = (p) => {
  if (p >= 1 && p <= totalPages.value) {
    page.value = p;
    loadAccounts(p);
  }
};

const createAccount = async () => {
  formError.value = '';
  formSuccess.value = '';
  submitting.value = true;
  try {
    const payload = {
      username: form.username,
      password: form.password,
      full_name: form.full_name,
      role: form.role,
      department: form.department,
      tenant_id: form.tenant_id || 'hospital-a',
      title: form.title,
      patient_id: needsPatientId.value ? form.patient_id : null,
    };
    const { data } = await axios.post('/api/v1/auth/accounts', payload);
    formSuccess.value = `Đã cấp tài khoản '${data.account.username}' (${data.account.role}) thành công!`;
    form.username = '';
    form.password = '';
    form.full_name = '';
    form.patient_id = '';
    form.title = '';
    await loadAccounts();
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Không thể tạo tài khoản.';
  } finally {
    submitting.value = false;
  }
};

const toggleStatus = async (username, action) => {
  formError.value = '';
  formSuccess.value = '';
  try {
    await axios.post(`/api/v1/auth/accounts/${encodeURIComponent(username)}/${action}`);
    await loadAccounts();
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Thao tác thất bại.';
  }
};

onMounted(loadAccounts);
</script>
