<template>
  <div class="space-y-6">
    <!-- Header banner -->
    <div class="p-5 rounded-2xl border transition-colors shadow-xs"
         :class="isDark ? 'bg-slate-900/60 border-rose-500/30' : 'bg-white border-rose-200'">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div class="flex items-center space-x-2">
            <span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono"
                  :class="isDark ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-200'">
              Zone Z2 Untrusted Storage
            </span>
            <h2 class="text-lg font-bold" :class="isDark ? 'text-white' : 'text-slate-900'">Góc nhìn Cloud DBA &amp; Kiểm toán Bảo mật Bản mã</h2>
          </div>
          <p class="text-xs mt-1" :class="isDark ? 'text-slate-300' : 'text-slate-600'">
            Bằng chứng an ninh (Security Proof): Dù kẻ tấn công hoặc Quản trị viên DBMS Đám mây có toàn quyền truy cập cơ sở dữ liệu MongoDB 7.0, họ <strong>chỉ thấy duy nhất các chuỗi Base64 Ciphertext vô nghĩa</strong> và không thể trích xuất DEK bản rõ.
          </p>
        </div>

        <button
          @click="loadDbaRecords"
          :disabled="loading"
          class="px-3.5 py-2 text-xs font-semibold rounded-xl border transition shadow-xs self-start sm:self-auto"
          :class="isDark
            ? 'bg-slate-800 hover:bg-slate-750 text-slate-200 border-slate-700'
            : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'"
        >
          {{ loading ? 'Đang đọc MongoDB...' : '↻ Tải lại dữ liệu MongoDB thô' }}
        </button>
      </div>
    </div>

    <!-- Security Comparison Cards: Plaintext vs Ciphertext -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
      <!-- Authorized Z0/Z1 View -->
      <div class="rounded-2xl p-5 space-y-3 border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/60 border-teal-500/30' : 'bg-white border-teal-200'">
        <div class="flex items-center justify-between pb-2 border-b"
             :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <span class="font-bold flex items-center space-x-1.5"
                :class="isDark ? 'text-teal-400' : 'text-teal-800'">
            <span class="w-2.5 h-2.5 rounded-full bg-teal-500"></span>
            <span>Góc nhìn Bác sĩ Điều trị (Zone Z0/Z1 - Authorized)</span>
          </span>
          <span class="text-[10px] font-mono text-slate-400">Đã giải mã qua DEK hợp lệ</span>
        </div>

        <div class="space-y-2 font-mono text-[11px]">
          <div class="p-2.5 rounded-xl border"
               :class="isDark ? 'bg-slate-850 border-slate-800' : 'bg-slate-50 border-slate-200'">
            <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Họ và tên bệnh nhân:</div>
            <div class="font-bold" :class="isDark ? 'text-slate-100' : 'text-slate-900'">Luong Thanh Hai (rec-pat-001)</div>
          </div>
          <div class="p-2.5 rounded-xl border"
               :class="isDark ? 'bg-slate-850 border-slate-800' : 'bg-slate-50 border-slate-200'">
            <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Chẩn đoán (Diagnosis):</div>
            <div class="text-teal-600 dark:text-teal-300 font-semibold">G43.9 Dau nua dau Migraine khong bien chung</div>
          </div>
          <div class="p-2.5 rounded-xl border"
               :class="isDark ? 'bg-slate-850 border-slate-800' : 'bg-slate-50 border-slate-200'">
            <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Ghi chú lâm sàng (Notes):</div>
            <div class="truncate" :class="isDark ? 'text-slate-300' : 'text-slate-700'">Dau nua dau ben trai giat theo nhip mach, kem buon non va so anh sang...</div>
          </div>
        </div>
      </div>

      <!-- Cloud DBA Zone Z2 View -->
      <div class="rounded-2xl p-5 space-y-3 border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/60 border-rose-500/30' : 'bg-white border-rose-200'">
        <div class="flex items-center justify-between pb-2 border-b"
             :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <span class="font-bold text-rose-500 flex items-center space-x-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
            <span>Góc nhìn Cloud DBA (Zone Z2 - Untrusted DB Host)</span>
          </span>
          <span class="text-[10px] font-mono font-bold text-rose-500">Zero Plaintext / Pure Ciphertext</span>
        </div>

        <div class="space-y-2 font-mono text-[11px]">
          <div class="p-2.5 rounded-xl border"
               :class="isDark ? 'bg-slate-950 border-slate-800' : 'bg-rose-50/50 border-rose-100'">
            <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Họ và tên bệnh nhân (Ciphertext):</div>
            <div class="text-rose-500 truncate">7qW9kL2x... (AES-256-GCM + Tag)</div>
          </div>
          <div class="p-2.5 rounded-xl border"
               :class="isDark ? 'bg-slate-950 border-slate-800' : 'bg-rose-50/50 border-rose-100'">
            <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Chẩn đoán (Ciphertext + Blind Index):</div>
            <div class="text-rose-500 truncate">hX49pM11a... / HMAC: b92a8e74f1...</div>
          </div>
          <div class="p-2.5 rounded-xl border"
               :class="isDark ? 'bg-slate-950 border-slate-800' : 'bg-rose-50/50 border-rose-100'">
            <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Ghi chú lâm sàng (Ciphertext):</div>
            <div class="text-rose-500 truncate">k0PpL8z9vR22... (Length: 176 bytes)</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Raw MongoDB Patients Table -->
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold flex items-center space-x-2"
            :class="isDark ? 'text-white' : 'text-slate-900'">
          <span>Tài liệu thô trong MongoDB Collection:</span>
          <code class="text-teal-600 dark:text-emerald-400 font-mono text-xs">encrypted_patients</code>
        </h3>
        <span class="text-xs font-mono" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
          {{ rawData?.total_records || 0 }} bản ghi mã hóa
        </span>
      </div>

      <div class="overflow-x-auto rounded-2xl border transition-colors shadow-xs"
           :class="isDark ? 'border-slate-800 bg-slate-900/40' : 'border-slate-200 bg-white'">
        <table class="w-full text-left border-collapse font-mono text-xs">
          <thead>
            <tr class="border-b text-[11px] font-semibold uppercase"
                :class="isDark ? 'border-slate-800 bg-slate-850/80 text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-600'">
              <th class="py-3 px-4">record_id</th>
              <th class="py-3 px-4">capsule_id</th>
              <th class="py-3 px-4">diagnosis_bidx (HMAC)</th>
              <th class="py-3 px-4">envelopes (AES-256-GCM)</th>
              <th class="py-3 px-4">updated_at</th>
            </tr>
          </thead>
          <tbody class="divide-y text-[11px]"
                 :class="isDark ? 'divide-slate-800/60' : 'divide-slate-200'">
            <tr
              v-for="rec in rawData?.raw_patients"
              :key="rec.record_id"
              class="transition cursor-pointer"
              :class="isDark ? 'hover:bg-slate-850/50' : 'hover:bg-slate-50'"
              @click="selectedRawDoc = rec"
            >
              <td class="py-3 px-4 text-teal-600 dark:text-emerald-400 font-bold">{{ rec.record_id }}</td>
              <td class="py-3 px-4 text-purple-600 dark:text-purple-400 truncate max-w-[140px]">{{ rec.capsule_id }}</td>
              <td class="py-3 px-4 text-amber-600 dark:text-amber-400 truncate max-w-[160px]">{{ rec.diagnosis_bidx || '—' }}</td>
              <td class="py-3 px-4">
                <span class="px-2 py-0.5 rounded text-[10px]"
                      :class="isDark ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-700'">
                  {{ Object.keys(rec.envelopes || {}).length }} fields encrypted
                </span>
              </td>
              <td class="py-3 px-4 text-[10px] text-slate-400">{{ rec.updated_at }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Raw MongoDB Key Capsules Table -->
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold flex items-center space-x-2"
            :class="isDark ? 'text-white' : 'text-slate-900'">
          <span>Tài liệu thô trong MongoDB Collection:</span>
          <code class="text-purple-600 dark:text-purple-400 font-mono text-xs">key_capsules</code>
        </h3>
        <span class="text-xs font-mono" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
          Bọc bởi KEK Transit (Zero Raw DEK in DB)
        </span>
      </div>

      <div class="overflow-x-auto rounded-2xl border transition-colors shadow-xs"
           :class="isDark ? 'border-slate-800 bg-slate-900/40' : 'border-slate-200 bg-white'">
        <table class="w-full text-left border-collapse font-mono text-xs">
          <thead>
            <tr class="border-b text-[11px] font-semibold uppercase"
                :class="isDark ? 'border-slate-800 bg-slate-850/80 text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-600'">
              <th class="py-3 px-4">capsule_id</th>
              <th class="py-3 px-4">tenant_id</th>
              <th class="py-3 px-4">wrapped_dek (Vault Transit)</th>
              <th class="py-3 px-4">kek_version</th>
              <th class="py-3 px-4">bound_context</th>
            </tr>
          </thead>
          <tbody class="divide-y text-[11px]"
                 :class="isDark ? 'divide-slate-800/60' : 'divide-slate-200'">
            <tr
              v-for="cap in rawData?.raw_capsules?.slice(0, 5)"
              :key="cap.capsule_id"
              class="transition"
              :class="isDark ? 'hover:bg-slate-850/50' : 'hover:bg-slate-50'"
            >
              <td class="py-3 px-4 text-purple-600 dark:text-purple-400 font-bold truncate max-w-[150px]">{{ cap.capsule_id }}</td>
              <td class="py-3 px-4" :class="isDark ? 'text-slate-300' : 'text-slate-700'">{{ cap.tenant_id }}</td>
              <td class="py-3 px-4 text-rose-500 truncate max-w-[200px]">{{ cap.wrapped_dek }}</td>
              <td class="py-3 px-4 text-teal-600 dark:text-emerald-400 font-bold">v{{ cap.kek_version }}</td>
              <td class="py-3 px-4 text-[10px] text-slate-400 truncate max-w-[200px]">
                {{ JSON.stringify(cap.bound_object_context) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Raw Document Inspector Modal -->
    <div
      v-if="selectedRawDoc"
      class="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      @click.self="selectedRawDoc = null"
    >
      <div class="rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl text-xs font-mono border"
           :class="isDark ? 'bg-slate-900 border-slate-800 text-slate-100' : 'bg-white border-slate-200 text-slate-800'">
        <div class="flex items-center justify-between pb-3 border-b"
             :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <h3 class="text-sm font-bold" :class="isDark ? 'text-white' : 'text-slate-900'">
            Chi tiết Bản ghi BSON thô trong MongoDB: {{ selectedRawDoc.record_id }}
          </h3>
          <button @click="selectedRawDoc = null" class="text-slate-400 hover:text-slate-600 dark:hover:text-white">✕</button>
        </div>

        <div class="space-y-3 max-h-[70vh] overflow-y-auto">
          <pre class="p-4 rounded-xl border text-[11px] overflow-x-auto leading-relaxed"
               :class="isDark ? 'bg-slate-950 border-slate-800 text-emerald-300' : 'bg-slate-50 border-slate-200 text-emerald-800'">{{ JSON.stringify(selectedRawDoc, null, 2) }}</pre>
        </div>

        <div class="flex justify-end pt-2 border-t"
             :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <button
            @click="selectedRawDoc = null"
            class="px-4 py-2 rounded-xl text-xs font-semibold font-sans border transition shadow-xs"
            :class="isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700' : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['toast']);

const loading = ref(false);
const rawData = ref(null);
const selectedRawDoc = ref(null);

onMounted(() => {
  loadDbaRecords();
});

async function loadDbaRecords() {
  loading.value = true;
  try {
    const res = await axios.get('/api/v1/dba/raw-records');
    rawData.value = res.data;
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Không thể tải dữ liệu kiểm toán DBA',
    });
  } finally {
    loading.value = false;
  }
}
</script>
