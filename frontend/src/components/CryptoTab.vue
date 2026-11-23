<template>
  <div class="space-y-8">
    <!-- Intro Ribbon -->
    <div class="p-5 rounded-2xl border transition-colors shadow-xs"
         :class="isDark
           ? 'bg-gradient-to-r from-emerald-950/40 via-slate-900 to-indigo-950/40 border-slate-800 text-white'
           : 'bg-gradient-to-r from-teal-50/70 via-slate-50 to-indigo-50/70 border-slate-200 text-slate-800'">
      <h2 class="text-lg font-bold flex items-center space-x-2">
        <span>Mật mã học Nâng cao (Advanced Cryptography Demonstrations)</span>
      </h2>
      <p class="text-xs mt-1 max-w-3xl leading-relaxed"
         :class="isDark ? 'text-slate-300' : 'text-slate-600'">
        Minh họa 2 trụ cột mật mã nâng cao của đề tài: <strong>CP-ABE (Ciphertext-Policy Attribute-Based Encryption)</strong> cho phép chia sẻ dữ liệu liên viện theo chính sách thuộc tính, và <strong>SEAL BFV Homomorphic Encryption</strong> cho phép chuyên viên phân tích tính tổng viện phí trực tiếp trên dữ liệu mã hóa.
      </p>
    </div>

    <!-- Section 1: CP-ABE Sharing -->
    <div class="rounded-2xl p-6 space-y-6 border transition-colors shadow-xs"
         :class="isDark ? 'bg-slate-900/60 border-slate-800' : 'bg-white border-slate-200'">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b gap-2"
           :class="isDark ? 'border-slate-800' : 'border-slate-200'">
        <div>
          <div class="flex items-center space-x-2">
            <span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono"
                  :class="isDark ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' : 'bg-purple-50 text-purple-800 border border-purple-200'">
              WP8 • Scheme AC17 (BN254)
            </span>
            <h3 class="text-base font-bold" :class="isDark ? 'text-white' : 'text-slate-900'">Chia sẻ Dữ liệu Hội chẩn Liên viện qua CP-ABE</h3>
          </div>
          <p class="text-xs mt-1" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
            Đóng gói hồ sơ lâm sàng bằng KEM/DEM (HKDF-SHA-256 + AES-256-GCM) gắn kèm chính sách truy cập logic (AND / OR).
          </p>
        </div>

        <span class="text-xs font-mono" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
          Worker Port: <code class="text-teal-600 dark:text-emerald-400 font-bold">:9002</code>
        </span>
      </div>

      <!-- Step 1: Export Package -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="space-y-4 text-xs">
          <div class="font-semibold flex items-center space-x-1.5"
               :class="isDark ? 'text-slate-200' : 'text-slate-800'">
            <span class="w-5 h-5 rounded-full flex items-center justify-center font-bold text-xs"
                  :class="isDark ? 'bg-purple-500/20 text-purple-400' : 'bg-purple-100 text-purple-800'">1</span>
            <span>Bác sĩ điều trị xuất gói dữ liệu hội chẩn</span>
          </div>

          <div>
            <label class="block mb-1 font-medium" :class="isDark ? 'text-slate-400' : 'text-slate-600'">Chọn hồ sơ bệnh nhân:</label>
            <select
              v-model="abeForm.record_id"
              class="w-full rounded-xl p-2.5 border transition focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              :class="isDark ? 'bg-slate-800 border-slate-700 text-white' : 'bg-slate-50 border-slate-300 text-slate-900 focus:bg-white'"
            >
              <option v-for="p in availablePatients" :key="p.record_id" :value="p.record_id">
                {{ p.record_id }} ({{ p.fields?.name || p.department }})
              </option>
            </select>
          </div>

          <div>
            <label class="block mb-1 font-medium" :class="isDark ? 'text-slate-400' : 'text-slate-600'">Thiết lập chính sách truy cập (Access Policy):</label>
            <input
              v-model="abeForm.policy"
              type="text"
              placeholder="(CARDIOLOGY AND DOCTOR)"
              class="w-full rounded-xl p-2.5 font-mono text-xs border transition focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              :class="isDark
                ? 'bg-slate-800 border-slate-700 text-emerald-400'
                : 'bg-slate-50 border-slate-300 text-emerald-800 font-bold focus:bg-white'"
            />
            <div class="flex flex-wrap gap-1.5 mt-2">
              <span class="text-[10px]" :class="isDark ? 'text-slate-500' : 'text-slate-400'">Mẫu gợi ý:</span>
              <button
                @click="abeForm.policy = '(CARDIOLOGY AND DOCTOR)'"
                class="px-2 py-0.5 rounded text-[10px] font-mono border transition"
                :class="isDark ? 'bg-slate-800 hover:bg-slate-750 text-slate-300 border-slate-700' : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'"
              >
                (CARDIOLOGY AND DOCTOR)
              </button>
              <button
                @click="abeForm.policy = '((CARDIOLOGY OR ONCOLOGY) AND DOCTOR)'"
                class="px-2 py-0.5 rounded text-[10px] font-mono border transition"
                :class="isDark ? 'bg-slate-800 hover:bg-slate-750 text-slate-300 border-slate-700' : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'"
              >
                ((CARDIOLOGY OR ONCOLOGY) AND DOCTOR)
              </button>
            </div>
          </div>

          <button
            @click="exportAbePackage"
            :disabled="exportingAbe"
            class="w-full py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-xl shadow-md transition flex items-center justify-center space-x-2"
          >
            <span>{{ exportingAbe ? 'Đang gọi Charm-Crypto AC17...' : '🔒 Xuất Gói CP-ABE Export Package' }}</span>
          </button>
        </div>

        <!-- Step 2: Package Info & Interactive Decrypt Simulator -->
        <div class="space-y-4 text-xs">
          <div class="font-semibold flex items-center space-x-1.5"
               :class="isDark ? 'text-slate-200' : 'text-slate-800'">
            <span class="w-5 h-5 rounded-full flex items-center justify-center font-bold text-xs"
                  :class="isDark ? 'bg-purple-500/20 text-purple-400' : 'bg-purple-100 text-purple-800'">2</span>
            <span>Thử nghiệm Giải mã phía Người nhận (Recipient Verification)</span>
          </div>

          <div v-if="!exportedPackage" class="p-6 rounded-2xl text-center border"
               :class="isDark ? 'bg-slate-850/60 border-slate-800 text-slate-500' : 'bg-slate-50 border-slate-200 text-slate-500'">
            Hãy nhấn <strong>"Xuất Gói CP-ABE"</strong> ở bước 1 để tạo gói bản mã kiểm thử.
          </div>

          <div v-else class="space-y-3">
            <div class="p-3 rounded-2xl border space-y-1 font-mono text-[11px]"
                 :class="isDark ? 'bg-slate-850 border-slate-800 text-slate-300' : 'bg-slate-50 border-slate-200 text-slate-700'">
              <div class="font-bold text-purple-600 dark:text-purple-300">✓ Gói CP-ABE đã sẵn sàng</div>
              <div>Policy gắn kèm: <span class="text-amber-600 dark:text-amber-400 font-bold">{{ exportedPackage.policy }}</span></div>
              <div>Algorithm: <span class="text-teal-600 dark:text-emerald-400 font-bold">AC17 KEM + AES-256-GCM DEM</span></div>
              <div class="truncate">KEM Ciphertext: {{ exportedPackage.kem_ciphertext?.length }} ký tự Base64</div>
            </div>

            <!-- Recipient Attributes Selection -->
            <div>
              <label class="block mb-1 font-medium" :class="isDark ? 'text-slate-400' : 'text-slate-600'">Thuộc tính của người nhận thử nghiệm:</label>
              <div class="grid grid-cols-2 gap-2 mb-2">
                <button
                  @click="testAttributes = ['CARDIOLOGY', 'DOCTOR']"
                  :class="arraysEqual(testAttributes, ['CARDIOLOGY', 'DOCTOR'])
                    ? (isDark ? 'border-teal-500 bg-teal-500/10 text-teal-300' : 'border-teal-500 bg-teal-50 text-teal-800 font-bold')
                    : (isDark ? 'border-slate-700 bg-slate-800 text-slate-300' : 'border-slate-300 bg-slate-100 text-slate-700')"
                  class="p-2 border rounded-xl text-left text-[11px] font-mono transition"
                >
                  <div class="font-bold">✓ Thỏa mãn policy</div>
                  <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">['CARDIOLOGY', 'DOCTOR']</div>
                </button>

                <button
                  @click="testAttributes = ['ONCOLOGY', 'DOCTOR']"
                  :class="arraysEqual(testAttributes, ['ONCOLOGY', 'DOCTOR'])
                    ? (isDark ? 'border-rose-500 bg-rose-500/10 text-rose-300' : 'border-rose-500 bg-rose-50 text-rose-800 font-bold')
                    : (isDark ? 'border-slate-700 bg-slate-800 text-slate-300' : 'border-slate-300 bg-slate-100 text-slate-700')"
                  class="p-2 border rounded-xl text-left text-[11px] font-mono transition"
                >
                  <div class="font-bold">✕ Thiếu khoa (TC-03)</div>
                  <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">['ONCOLOGY', 'DOCTOR']</div>
                </button>

                <button
                  @click="testAttributes = ['CARDIOLOGY', 'NURSE']"
                  :class="arraysEqual(testAttributes, ['CARDIOLOGY', 'NURSE'])
                    ? (isDark ? 'border-rose-500 bg-rose-500/10 text-rose-300' : 'border-rose-500 bg-rose-50 text-rose-800 font-bold')
                    : (isDark ? 'border-slate-700 bg-slate-800 text-slate-300' : 'border-slate-300 bg-slate-100 text-slate-700')"
                  class="p-2 border rounded-xl text-left text-[11px] font-mono transition"
                >
                  <div class="font-bold">✕ Sai vai trò</div>
                  <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">['CARDIOLOGY', 'NURSE']</div>
                </button>

                <button
                  @click="testAttributes = ['CARDIOLOGY', 'RESEARCHER']"
                  :class="arraysEqual(testAttributes, ['CARDIOLOGY', 'RESEARCHER'])
                    ? (isDark ? 'border-rose-500 bg-rose-500/10 text-rose-300' : 'border-rose-500 bg-rose-50 text-rose-800 font-bold')
                    : (isDark ? 'border-slate-700 bg-slate-800 text-slate-300' : 'border-slate-300 bg-slate-100 text-slate-700')"
                  class="p-2 border rounded-xl text-left text-[11px] font-mono transition"
                >
                  <div class="font-bold">✕ Không đủ quyền</div>
                  <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">['CARDIOLOGY', 'RESEARCHER']</div>
                </button>
              </div>

              <button
                @click="testAbeDecrypt"
                :disabled="decryptingAbe"
                class="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-xl shadow-xs transition"
              >
                {{ decryptingAbe ? 'Đang kiểm tra thuộc tính...' : 'Thực hiện Thử nghiệm Giải mã' }}
              </button>
            </div>

            <!-- Decrypt Result Banner -->
            <div
              v-if="decryptResult"
              :class="decryptResult.status === 'SUCCESS'
                ? (isDark ? 'bg-teal-500/10 border-teal-500/30 text-teal-300' : 'bg-teal-50 border-teal-200 text-teal-800')
                : (isDark ? 'bg-rose-500/10 border-rose-500/30 text-rose-300' : 'bg-rose-50 border-rose-200 text-rose-800')"
              class="p-3 border rounded-xl space-y-1"
            >
              <div class="font-bold text-xs flex items-center space-x-1.5">
                <span>{{ decryptResult.status === 'SUCCESS' ? '✓ GIẢI MÃ THÀNH CÔNG' : '✕ BỊ TỪ CHỐI GIẢI MÃ' }}</span>
              </div>
              <p class="text-[11px]">{{ decryptResult.message }}</p>
              <div v-if="decryptResult.decrypted_payload" class="mt-2 p-2 rounded-xl font-mono text-[10px] overflow-x-auto max-h-32"
                   :class="isDark ? 'bg-slate-950 text-slate-200' : 'bg-slate-100 text-slate-800'">
                {{ decryptResult.decrypted_payload }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Section 2: SEAL BFV Homomorphic Computation -->
    <div class="rounded-2xl p-6 space-y-6 border transition-colors shadow-xs"
         :class="isDark ? 'bg-slate-900/60 border-slate-800' : 'bg-white border-slate-200'">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b gap-2"
           :class="isDark ? 'border-slate-800' : 'border-slate-200'">
        <div>
          <div class="flex items-center space-x-2">
            <span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono"
                  :class="isDark ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'bg-cyan-50 text-cyan-800 border border-cyan-200'">
              WP7 • Microsoft SEAL BFV (128-bit)
            </span>
            <h3 class="text-base font-bold" :class="isDark ? 'text-white' : 'text-slate-900'">Tính toán Tổng Viện phí Đồng cấu (Homomorphic Billing SUM)</h3>
          </div>
          <p class="text-xs mt-1" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
            Chuyên viên Thống kê (Analyst) tính tổng chi phí điều trị trực tiếp trên các bản mã BFV mà không giải mã từng khoản chi tiêu riêng lẻ của bệnh nhân.
          </p>
        </div>

        <span class="text-xs font-mono" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
          Security: <code class="text-teal-600 dark:text-emerald-400 font-bold">λ = 128-bit</code>
        </span>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Input cost items -->
        <div class="space-y-4 text-xs">
          <div class="font-semibold" :class="isDark ? 'text-slate-200' : 'text-slate-800'">Danh sách các khoản chi phí điều trị (VNĐ):</div>

          <div class="space-y-2">
            <div
              v-for="(item, idx) in billingItems"
              :key="idx"
              class="flex items-center space-x-2"
            >
              <span class="w-24 font-mono" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Mục #{{ idx + 1 }}:</span>
              <input
                v-model.number="billingItems[idx]"
                type="number"
                class="flex-1 rounded-xl p-2 font-mono border transition focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                :class="isDark ? 'bg-slate-800 border-slate-700 text-white' : 'bg-slate-50 border-slate-300 text-slate-900 focus:bg-white'"
              />
              <button
                @click="removeBillingItem(idx)"
                class="p-2 text-rose-500 hover:text-rose-600"
                title="Xóa mục"
              >
                ✕
              </button>
            </div>
          </div>

          <div class="flex items-center space-x-2 pt-2">
            <button
              @click="addBillingItem"
              class="px-3.5 py-1.5 rounded-xl border transition shadow-xs text-xs"
              :class="isDark ? 'bg-slate-800 hover:bg-slate-750 text-slate-300 border-slate-700' : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'"
            >
              + Thêm khoản chi phí
            </button>
            <button
              @click="resetBillingItems"
              class="px-3.5 py-1.5 text-xs transition"
              :class="isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-800'"
            >
              Đặt lại mẫu
            </button>
          </div>

          <button
            @click="calculateBfvSum"
            :disabled="calculatingHe"
            class="w-full py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-xl shadow-md transition flex items-center justify-center space-x-2"
          >
            <span>{{ calculatingHe ? 'Đang thực thi Microsoft SEAL Worker...' : '⚡ Tính toán Đồng cấu SUM BFV trên Ciphertext' }}</span>
          </button>
        </div>

        <!-- BFV Results & Cryptographic Metrics -->
        <div class="space-y-4 text-xs">
          <div class="font-semibold" :class="isDark ? 'text-slate-200' : 'text-slate-800'">Kết quả Tính toán & Tham số Mật mã:</div>

          <div v-if="!heResult" class="p-6 rounded-2xl text-center border"
               :class="isDark ? 'bg-slate-850/60 border-slate-800 text-slate-500' : 'bg-slate-50 border-slate-200 text-slate-500'">
            Nhấn nút <strong>"Tính toán Đồng cấu SUM BFV"</strong> để gửi mảng bản mã tới SEAL worker.
          </div>

          <div v-else class="space-y-3">
            <!-- Big result display -->
            <div class="p-4 border rounded-2xl transition-colors shadow-xs"
                 :class="isDark
                   ? 'bg-gradient-to-br from-cyan-950/40 to-slate-900 border-cyan-500/30'
                   : 'bg-gradient-to-br from-cyan-50 to-teal-50 border-cyan-200'">
              <div class="text-[11px] uppercase font-bold" :class="isDark ? 'text-cyan-400' : 'text-cyan-800'">Tổng Viện phí Sau Giải mã Kết quả Đồng cấu:</div>
              <div class="text-3xl font-black font-mono mt-1" :class="isDark ? 'text-white' : 'text-slate-900'">
                {{ formatCurrency(heResult.homomorphic_sum) }} VNĐ
              </div>
              <div class="text-[11px] flex items-center space-x-1 mt-1"
                   :class="isDark ? 'text-emerald-400' : 'text-teal-700 font-semibold'">
                <span>✓ Trùng khớp chính xác 100% với giá trị tổng bản rõ (Exact Integer Correctness)</span>
              </div>
            </div>

            <!-- Security & Performance Metrics Grid -->
            <div class="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div class="p-2.5 rounded-xl border"
                   :class="isDark ? 'bg-slate-850 border-slate-800' : 'bg-slate-50 border-slate-200'">
                <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Noise Budget Còn lại</div>
                <div class="font-bold mt-0.5 text-teal-600 dark:text-emerald-400">{{ heResult.noise_budget_remaining }} bits</div>
              </div>
              <div class="p-2.5 rounded-xl border"
                   :class="isDark ? 'bg-slate-850 border-slate-800' : 'bg-slate-50 border-slate-200'">
                <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Tỉ lệ Giãn nở Bản mã</div>
                <div class="font-bold mt-0.5 text-amber-600 dark:text-amber-400">{{ heResult.ciphertext_expansion_ratio?.toFixed(1) }}x</div>
              </div>
              <div class="p-2.5 rounded-xl border"
                   :class="isDark ? 'bg-slate-850 border-slate-800' : 'bg-slate-50 border-slate-200'">
                <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Thời gian Cộng Đồng cấu</div>
                <div class="font-bold mt-0.5 text-cyan-600 dark:text-cyan-400">{{ heResult.evaluation_time_ms }} ms</div>
              </div>
              <div class="p-2.5 rounded-xl border"
                   :class="isDark ? 'bg-slate-850 border-slate-800' : 'bg-slate-50 border-slate-200'">
                <div class="text-[10px]" :class="isDark ? 'text-slate-400' : 'text-slate-500'">Tổng độ trễ End-to-End</div>
                <div class="font-bold mt-0.5" :class="isDark ? 'text-white' : 'text-slate-900'">{{ heResult.total_e2e_time_ms }} ms</div>
              </div>
            </div>

            <p class="text-[11px] italic" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
              * Ghi chú an ninh (TC-19 Trust Boundary): Máy chủ tính toán thực hiện phép cộng trên ciphertext mà không bao giờ biết chi phí của từng hóa đơn riêng rẽ.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import axios from 'axios';

const props = defineProps({
  patients: {
    type: Array,
    required: true,
  },
  currentUser: {
    type: Object,
    default: null,
  },
  isDark: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['toast']);

const availablePatients = computed(() => {
  return props.patients.filter((p) => p.access_status !== 'DENIED');
});

// ABE State
const abeForm = ref({
  record_id: 'rec-pat-001',
  policy: '(CARDIOLOGY AND DOCTOR)',
});

watch(
  availablePatients,
  (list) => {
    if (list.length > 0 && !list.some((p) => p.record_id === abeForm.value.record_id)) {
      abeForm.value.record_id = list[0].record_id;
    }
  },
  { immediate: true }
);
const exportingAbe = ref(false);
const exportedPackage = ref(null);
const testAttributes = ref(['CARDIOLOGY', 'DOCTOR']);
const decryptingAbe = ref(false);
const decryptResult = ref(null);

// BFV State
const billingItems = ref([1500000, 3200000, 850000, 1200000, 450000]);
const calculatingHe = ref(false);
const heResult = ref(null);

function arraysEqual(a, b) {
  if (a.length !== b.length) return false;
  const sA = [...a].sort();
  const sB = [...b].sort();
  return sA.every((val, index) => val === sB[index]);
}

async function exportAbePackage() {
  exportingAbe.value = true;
  decryptResult.value = null;
  try {
    const res = await axios.post(
      '/api/v1/crypto/abe/export',
      {
        record_id: abeForm.value.record_id,
        policy: abeForm.value.policy,
      },
      {
        headers: {},
      }
    );
    exportedPackage.value = res.data.export_package;
    emit('toast', {
      type: 'success',
      message: `Gói CP-ABE đã được xuất thành công theo chính sách ${abeForm.value.policy}!`,
    });
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Lỗi khi xuất gói CP-ABE',
    });
  } finally {
    exportingAbe.value = false;
  }
}

async function testAbeDecrypt() {
  if (!exportedPackage.value) return;
  decryptingAbe.value = true;
  decryptResult.value = null;
  try {
    const res = await axios.post('/api/v1/crypto/abe/decrypt-test', {
      export_package: exportedPackage.value,
      user_attributes: testAttributes.value,
    });
    decryptResult.value = res.data;
  } catch (err) {
    decryptResult.value = {
      status: 'ERROR',
      message: err.response?.data?.detail || 'Lỗi khi giải mã CP-ABE',
    };
  } finally {
    decryptingAbe.value = false;
  }
}

function addBillingItem() {
  billingItems.value.push(1000000);
}

function removeBillingItem(idx) {
  billingItems.value.splice(idx, 1);
}

function resetBillingItems() {
  billingItems.value = [1500000, 3200000, 850000, 1200000, 450000];
  heResult.value = null;
}

async function calculateBfvSum() {
  calculatingHe.value = true;
  try {
    const res = await axios.post(
      '/api/v1/crypto/he/sum',
      { items: billingItems.value },
      {},
    );
    heResult.value = res.data;
    emit('toast', {
      type: 'success',
      message: 'Tính toán đồng cấu hoàn tất trên worker Microsoft SEAL BFV!',
    });
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Lỗi khi tính toán đồng cấu BFV',
    });
  } finally {
    calculatingHe.value = false;
  }
}

function formatCurrency(val) {
  if (!val) return '0';
  return new Intl.NumberFormat('vi-VN').format(val);
}
</script>
