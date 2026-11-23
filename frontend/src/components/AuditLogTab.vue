<template>
  <div class="space-y-6">
    <!-- Header banner -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-5 rounded-2xl border transition-colors shadow-xs"
         :class="isDark ? 'bg-slate-900/60 border-slate-800' : 'bg-white border-slate-200'">
      <div>
        <h2 class="text-lg font-bold flex items-center space-x-2"
            :class="isDark ? 'text-white' : 'text-slate-900'">
          <span>Nhật ký Kiểm toán An ninh (Zone Z3 Audit Trail)</span>
          <span class="px-2 py-0.5 text-xs rounded font-semibold font-mono"
                :class="isDark ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'bg-cyan-50 text-cyan-800 border border-cyan-200'">
            F9 Metadata-Only
          </span>
        </h2>
        <p class="text-xs mt-1" :class="isDark ? 'text-slate-400' : 'text-slate-600'">
          Ghi nhận toàn bộ quyết định cấp quyền / từ chối của Gateway PEP. Tuyệt đối không lưu trữ bản rõ lâm sàng hay secret key.
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <select
          v-model="filterOutcome"
          class="text-xs rounded-xl px-3 py-2 border transition focus:outline-none focus:ring-2 focus:ring-cyan-500/50 shadow-xs"
          :class="isDark ? 'bg-slate-800 text-slate-200 border-slate-700' : 'bg-slate-50 text-slate-800 border-slate-300 focus:bg-white'"
        >
          <option value="ALL">Tất cả sự kiện</option>
          <option value="PERMITTED">Chỉ PERMITTED</option>
          <option value="DENIED">Chỉ DENIED (Vi phạm ABAC)</option>
        </select>

        <button
          @click="loadLogs"
          :disabled="loading"
          class="px-3.5 py-2 text-xs font-semibold rounded-xl border transition shadow-xs"
          :class="isDark ? 'bg-slate-800 hover:bg-slate-750 text-slate-200 border-slate-700' : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'"
        >
          {{ loading ? 'Đang đọc...' : '↻ Tải lại' }}
        </button>
      </div>
    </div>

    <!-- Logs Table -->
    <div class="overflow-x-auto rounded-2xl border transition-colors shadow-xs"
         :class="isDark ? 'border-slate-800 bg-slate-900/40' : 'border-slate-200 bg-white'">
      <table class="w-full text-left border-collapse font-mono text-xs">
        <thead>
          <tr class="border-b text-[11px] font-semibold uppercase"
              :class="isDark ? 'border-slate-800 bg-slate-850/80 text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-600'">
            <th class="py-3 px-4">Thời điểm (UTC)</th>
            <th class="py-3 px-4">Thao tác</th>
            <th class="py-3 px-4">Subject Role</th>
            <th class="py-3 px-4">Subject Hash (SHA-256)</th>
            <th class="py-3 px-4">Mã hồ sơ</th>
            <th class="py-3 px-4">Kết quả PEP</th>
            <th class="py-3 px-4">Lý do / Vi phạm</th>
          </tr>
        </thead>
        <tbody class="divide-y text-[11px]"
               :class="isDark ? 'divide-slate-800/60' : 'divide-slate-200'">
          <tr
            v-for="(evt, idx) in filteredLogs"
            :key="idx"
            class="transition"
            :class="isDark ? 'hover:bg-slate-850/50' : 'hover:bg-slate-50'"
          >
            <td class="py-3 px-4 whitespace-nowrap text-slate-400">
              {{ formatTime(evt.timestamp) }}
            </td>
            <td class="py-3 px-4 font-bold" :class="isDark ? 'text-slate-200' : 'text-slate-800'">
              {{ evt.operation }}
            </td>
            <td class="py-3 px-4">
              <span class="px-2 py-0.5 rounded text-[10px]"
                    :class="isDark ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-700'">
                {{ evt.subject_role }}
              </span>
            </td>
            <td class="py-3 px-4 text-slate-400 truncate max-w-[120px]" :title="evt.subject_hash">
              {{ evt.subject_hash?.slice(0, 12) }}...
            </td>
            <td class="py-3 px-4 text-teal-600 dark:text-emerald-400 font-bold">
              {{ evt.record_id }}
            </td>
            <td class="py-3 px-4">
              <span
                v-if="evt.outcome === 'PERMITTED'"
                class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold"
                :class="isDark ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20' : 'bg-teal-50 text-teal-800 border border-teal-200'"
              >
                ● PERMITTED
              </span>
              <span
                v-else
                class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold"
                :class="isDark ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-rose-50 text-rose-700 border border-rose-200'"
              >
                ✕ DENIED
              </span>
            </td>
            <td class="py-3 px-4 max-w-xs truncate" :class="isDark ? 'text-slate-300' : 'text-slate-700'" :title="evt.reason">
              {{ evt.reason }}
            </td>
          </tr>

          <tr v-if="filteredLogs.length === 0">
            <td colspan="7" class="py-8 text-center text-xs font-sans italic"
                :class="isDark ? 'text-slate-500' : 'text-slate-400'">
              Chưa có sự kiện kiểm toán nào được ghi nhận.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['toast']);

const logs = ref([]);
const loading = ref(false);
const filterOutcome = ref('ALL');

onMounted(() => {
  loadLogs();
});

const filteredLogs = computed(() => {
  if (filterOutcome.value === 'ALL') {
    return logs.value;
  }
  return logs.value.filter((l) => l.outcome === filterOutcome.value);
});

async function loadLogs() {
  loading.value = true;
  try {
    const res = await axios.get('/api/v1/audit/logs');
    logs.value = (res.data.events || []).reverse();
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: 'Không thể đọc nhật ký kiểm toán',
    });
  } finally {
    loading.value = false;
  }
}

function formatTime(isoStr) {
  if (!isoStr) return '—';
  try {
    return new Date(isoStr).toLocaleTimeString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return isoStr;
  }
}
</script>
