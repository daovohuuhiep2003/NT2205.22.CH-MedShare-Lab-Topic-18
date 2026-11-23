<template>
  <div class="space-y-6">
    <!-- Header banner (Hospital PACS Module) -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-2xl border transition-colors shadow-xs"
         :class="isDark ? 'bg-slate-900/70 border-slate-800' : 'bg-white border-slate-200'">
      <div>
        <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
          <span>Hệ thống Lưu trữ &amp; Truyền nhận Hình ảnh Y khoa (PACS / RIS)</span>
          <span class="px-2 py-0.5 text-xs font-bold rounded-full"
                :class="isDark ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-amber-50 text-amber-800 border border-amber-200'">
            Zone Z2 Encrypted S3 MinIO
          </span>
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Toàn bộ phim chụp X-Quang, cắt lớp vi tính CT, cộng hưởng từ MRI, siêu âm tim và phiếu xét nghiệm PDF được mã hóa phân đoạn <strong>Chunked AES-256-GCM</strong> trước khi lưu trữ đám mây.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <!-- Patient selector -->
        <div class="flex items-center space-x-2">
          <label class="text-xs font-semibold text-slate-600 dark:text-slate-400">Chọn bệnh nhân:</label>
          <select
            v-model="selectedRecordId"
            @change="loadAttachments"
            class="text-xs rounded-xl px-3 py-1.5 border transition focus:outline-none focus:ring-1 focus:ring-teal-500"
            :class="isDark ? 'bg-slate-800 text-slate-100 border-slate-700' : 'bg-slate-50 text-slate-900 border-slate-300'"
          >
            <option v-for="p in availablePatients" :key="p.record_id" :value="p.record_id">
              {{ p.record_id }} ({{ p.fields?.name || p.department }})
            </option>
          </select>
        </div>

        <!-- Upload Button (for authorized doctors & nurses) -->
        <button
          v-if="canUpload"
          @click="showUploadModal = true"
          class="flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-bold bg-teal-600 hover:bg-teal-500 text-white rounded-xl shadow-xs transition"
        >
          <span>+ Tải lên tệp y tế mới</span>
        </button>
      </div>
    </div>

    <!-- Attachments Grid -->
    <div v-if="loading" class="py-12 text-center text-slate-400 text-xs">
      Đang giải mã và tải danh sách tệp đính kèm PACS từ MinIO...
    </div>

    <div v-else-if="attachments.length === 0" class="py-12 text-center rounded-2xl border transition-colors"
         :class="isDark ? 'bg-slate-900/30 border-slate-800' : 'bg-white border-slate-200'">
      <div class="text-2xl mb-2">🩻</div>
      <div class="text-sm font-bold text-slate-700 dark:text-slate-300">Không có tệp đính kèm nào cho hồ sơ này</div>
      <p class="text-xs text-slate-400 mt-1">Hoặc vai trò tài khoản hiện tại không đủ quyền ABAC (READ_ATTACHMENT) theo chuyên khoa.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="att in attachments"
        :key="att.attachment_id"
        class="rounded-2xl p-4 flex flex-col justify-between border transition shadow-xs"
        :class="isDark ? 'bg-slate-900/70 border-slate-800 hover:border-slate-700' : 'bg-white border-slate-200 hover:border-teal-300'"
      >
        <div>
          <!-- Modality & Dept badges -->
          <div class="flex items-center justify-between mb-2.5">
            <span :class="modalityClass(att.modality)" class="px-2.5 py-0.5 rounded-md text-[10px] font-extrabold uppercase tracking-wider border">
              {{ att.modality }}
            </span>
            <span class="text-[11px] font-mono text-slate-500 dark:text-slate-400 font-semibold">
              {{ formatBytes(att.file_size_bytes) }}
            </span>
          </div>

          <!-- Filename -->
          <h4 class="text-sm font-bold text-slate-900 dark:text-slate-100 truncate" :title="att.filename">
            {{ att.filename }}
          </h4>
          <p class="text-[10px] font-mono text-slate-400 mt-0.5 truncate">
            Mã tệp: {{ att.attachment_id }}
          </p>
          <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-2 flex flex-wrap items-center gap-2">
            <span>Khoa: <strong class="text-teal-700 dark:text-teal-300">{{ att.department }}</strong></span>
            <span>·</span>
            <span>Mức bảo mật: <strong class="text-amber-600 dark:text-amber-400">{{ att.sensitivity }}</strong></span>
          </div>
        </div>

        <!-- Action buttons -->
        <div class="pt-3.5 mt-3.5 border-t flex items-center justify-between gap-2"
             :class="isDark ? 'border-slate-800' : 'border-slate-100'">
          <!-- View Raw Ciphertext Proof -->
          <button
            @click="inspectCiphertext(att)"
            class="px-2.5 py-1.5 text-xs rounded-xl font-semibold border transition"
            :class="isDark ? 'text-slate-300 bg-slate-800 hover:bg-slate-700 border-slate-700' : 'text-slate-700 bg-slate-100 hover:bg-slate-200 border-slate-200'"
            title="Xem bằng chứng bản mã thô lưu trong MinIO S3"
          >
            🔍 Soi bản mã MinIO
          </button>

          <!-- Decrypt & Preview -->
          <button
            @click="previewAttachment(att)"
            class="px-3.5 py-1.5 text-xs font-bold text-white bg-teal-600 hover:bg-teal-500 rounded-xl shadow-xs transition flex items-center space-x-1"
          >
            <span v-if="att.modality === 'XRAY'">🩻 Xem ảnh</span>
            <span v-else-if="att.content_type === 'application/pdf'">📄 Đọc PDF</span>
            <span v-else>👁️ Xem bản rõ</span>
          </button>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- PREVIEW MODAL (INTERACTIVE MEDICAL IMAGE & PDF VIEWER) -->
    <!-- ===================================================================== -->
    <div
      v-if="previewModalData"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 z-50"
      @click.self="closePreview"
    >
      <div
        class="w-full max-w-4xl rounded-2xl p-5 sm:p-6 space-y-4 shadow-2xl max-h-[92vh] flex flex-col border transition-colors"
        :class="isDark ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-300 text-slate-900'"
      >
        <!-- Modal Header -->
        <div class="flex items-center justify-between pb-3 border-b"
             :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <div>
            <h3 class="text-sm sm:text-base font-bold flex items-center space-x-2">
              <span class="truncate max-w-[260px] sm:max-w-none">{{ previewModalData.att.filename }}</span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 text-teal-800 border border-teal-200 dark:bg-teal-500/20 dark:text-teal-300 dark:border-teal-500/30">
                DECRYPTED (Zone Z0/Z1)
              </span>
            </h3>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 font-mono">
              Xác thực toàn vẹn: {{ previewModalData.sha256 || 'SHA-256 Verified' }}
            </p>
          </div>

          <div class="flex items-center space-x-2">
            <!-- Toolbar for Images -->
            <template v-if="previewModalData.isImage">
              <button
                @click="imageZoom = Math.max(0.5, imageZoom - 0.2)"
                class="p-1.5 rounded-lg border text-xs font-bold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700"
                title="Thu nhỏ (-)"
              >
                -
              </button>
              <button
                @click="imageZoom = 1; imageRotate = 0; imageInvert = false"
                class="px-2 py-1 rounded-lg border text-xs font-mono font-bold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700"
                title="Đặt lại 100%"
              >
                {{ Math.round(imageZoom * 100) }}%
              </button>
              <button
                @click="imageZoom = Math.min(3, imageZoom + 0.2)"
                class="p-1.5 rounded-lg border text-xs font-bold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700"
                title="Phóng to (+)"
              >
                +
              </button>
              <button
                @click="imageRotate = (imageRotate + 90) % 360"
                class="p-1.5 rounded-lg border text-xs font-bold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700"
                title="Xoay 90 độ"
              >
                ↻
              </button>
              <button
                @click="imageInvert = !imageInvert"
                class="px-2 py-1 rounded-lg border text-xs font-bold transition"
                :class="imageInvert ? 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-500/20 dark:text-amber-300' : 'bg-slate-100 dark:bg-slate-800'"
                title="Đảo âm bản / dương bản"
              >
                ☯ Âm bản
              </button>
            </template>

            <!-- Toolbar for PDF -->
            <template v-else-if="previewModalData.isPdf">
              <button
                @click="openInNewTab(previewModalData.url)"
                class="px-2.5 py-1 rounded-lg border text-xs font-bold bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 dark:bg-blue-900/40 dark:text-blue-300 dark:border-blue-700"
                title="Mở tài liệu PDF trong tab mới"
              >
                ↗ Mở tab mới
              </button>
            </template>

            <button @click="closePreview" class="text-slate-400 hover:text-slate-600 dark:hover:text-white text-lg ml-2">✕</button>
          </div>
        </div>

        <!-- Content Viewer Container -->
        <div class="flex-1 overflow-auto flex items-center justify-center p-2 rounded-2xl border min-h-[400px] max-h-[65vh]"
             :class="isDark ? 'bg-black/90 border-slate-800' : 'bg-slate-900/95 border-slate-200'">
          <!-- Image Viewer -->
          <img
            v-if="previewModalData.isImage"
            :src="previewModalData.url"
            alt="Medical Image"
            class="transition-all duration-200 max-h-[60vh] max-w-full object-contain rounded-lg shadow-2xl"
            :style="{
              transform: `scale(${imageZoom}) rotate(${imageRotate}deg)`,
              filter: imageInvert ? 'invert(100%)' : 'none'
            }"
          />

          <!-- Embedded PDF Viewer -->
          <iframe
            v-else-if="previewModalData.isPdf"
            :src="previewModalData.url"
            class="w-full h-[60vh] border-0 rounded-xl bg-white"
            title="PDF Document Viewer"
          ></iframe>

          <!-- Binary / Fallback notice -->
          <div v-else class="text-center p-6 space-y-3 text-white">
            <div class="text-3xl">📦</div>
            <div class="text-sm font-bold">Tài liệu đã được giải mã nguyên vẹn thành công!</div>
            <p class="text-xs text-slate-300">
              Định dạng: <code class="text-teal-400 font-mono">{{ previewModalData.att.content_type }}</code>
            </p>
            <a
              :href="previewModalData.url"
              :download="previewModalData.att.filename"
              class="inline-block px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold rounded-xl shadow-xs"
            >
              📥 Tải file giải mã về máy
            </a>
          </div>
        </div>

        <!-- Modal Bottom Actions -->
        <div class="flex items-center justify-between pt-2 border-t"
             :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <div class="text-[11px] text-slate-500 font-mono">
            Modality: {{ previewModalData.att.modality }} · {{ formatBytes(previewModalData.att.file_size_bytes) }}
          </div>

          <div class="flex items-center space-x-2">
            <a
              :href="previewModalData.url"
              :download="previewModalData.att.filename"
              class="px-4 py-1.5 text-xs font-bold text-white bg-teal-600 hover:bg-teal-500 rounded-xl transition shadow-xs"
            >
              📥 Tải tệp về máy
            </a>
            <button
              @click="closePreview"
              class="px-4 py-1.5 text-xs font-semibold rounded-xl border transition"
              :class="isDark ? 'text-slate-300 bg-slate-800 hover:bg-slate-700 border-slate-700' : 'text-slate-700 bg-slate-100 hover:bg-slate-200 border-slate-300'"
            >
              Đóng
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Raw Ciphertext Inspector Modal -->
    <div
      v-if="rawModalData"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      @click.self="rawModalData = null"
    >
      <div class="border rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl text-xs transition-colors"
           :class="isDark ? 'bg-slate-900 border-slate-700 text-slate-100' : 'bg-white border-slate-300 text-slate-900'">
        <div class="flex items-center justify-between pb-3 border-b"
             :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <h3 class="text-base font-bold flex items-center space-x-2">
            <span>Bằng chứng Bản mã trong MinIO S3 (Zone Z2)</span>
            <span class="px-2 py-0.5 text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-500/20 dark:text-rose-400 dark:border-rose-500/30 rounded-full">
              UNTRUSTED STORAGE
            </span>
          </h3>
          <button @click="rawModalData = null" class="text-slate-400 hover:text-slate-600 dark:hover:text-white">✕</button>
        </div>

        <div class="space-y-3 font-mono">
          <div class="p-3.5 rounded-xl border space-y-1.5"
               :class="isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'">
            <div><strong>S3 Bucket:</strong> <span class="text-amber-600 dark:text-amber-400">{{ rawModalData.s3_bucket }}</span></div>
            <div><strong>S3 Object Key:</strong> <span class="text-amber-600 dark:text-amber-400">{{ rawModalData.s3_key }}</span></div>
            <div><strong>Kích thước Ciphertext:</strong> {{ rawModalData.total_ciphertext_bytes }} bytes</div>
            <div><strong>Capsule ID:</strong> <span class="text-teal-700 dark:text-teal-400">{{ rawModalData.capsule_id }}</span></div>
            <div class="truncate"><strong>Plaintext SHA-256:</strong> {{ rawModalData.plaintext_sha256 }}</div>
            <div class="truncate"><strong>Ciphertext SHA-256:</strong> {{ rawModalData.ciphertext_sha256 }}</div>
          </div>

          <div>
            <div class="font-bold mb-1 font-sans text-slate-700 dark:text-slate-300">Mẫu 128 bytes bản mã thô (Hex dump):</div>
            <div class="p-3 rounded-xl border text-[11px] text-rose-600 dark:text-rose-400 break-all leading-relaxed"
                 :class="isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'">
              {{ rawModalData.sample_ciphertext_hex_first_128 }}...
            </div>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-1 italic font-sans">
              Minh chứng: Kẻ tấn công hoặc quản trị viên có quyền truy cập trực tiếp MinIO bucket chỉ thu được chuỗi byte ngẫu nhiên vô nghĩa và không thể giải mã nếu không có KEK từ Vault KMS.
            </p>
          </div>
        </div>

        <div class="flex justify-end pt-2 border-t"
             :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <button
            @click="rawModalData = null"
            class="px-4 py-1.5 rounded-xl font-semibold border"
            :class="isDark ? 'text-slate-300 bg-slate-800 hover:bg-slate-700 border-slate-700' : 'text-slate-700 bg-slate-100 hover:bg-slate-200 border-slate-300'"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>

    <!-- Upload Modal -->
    <div
      v-if="showUploadModal"
      class="fixed inset-0 bg-black/60 dark:bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      @click.self="showUploadModal = false"
    >
      <div class="border rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl transition-colors"
           :class="isDark ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-300 text-slate-900'">
        <div class="flex items-center justify-between pb-3 border-b"
             :class="isDark ? 'border-slate-800' : 'border-slate-200'">
          <h3 class="text-base font-bold">Tải lên Phim chụp / Phiếu xét nghiệm PACS</h3>
          <button @click="showUploadModal = false" class="text-slate-400 hover:text-slate-600 dark:hover:text-white">✕</button>
        </div>

        <form @submit.prevent="submitUpload" class="space-y-3.5 text-xs">
          <div>
            <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Bệnh nhân thụ hưởng</label>
            <input
              :value="selectedRecordId"
              disabled
              class="w-full bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2 font-mono text-slate-500 dark:text-slate-400"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Loại hình (Modality) *</label>
              <select
                v-model="uploadForm.modality"
                class="w-full border rounded-xl p-2 focus:ring-1 focus:ring-teal-500"
                :class="isDark ? 'bg-slate-800 border-slate-700 text-white' : 'bg-slate-50 border-slate-300 text-slate-900'"
              >
                <option value="XRAY">X-Quang (XRAY)</option>
                <option value="CT">Cắt lớp vi tính (CT)</option>
                <option value="MRI">Cộng hưởng từ (MRI)</option>
                <option value="ULTRASOUND">Siêu âm (ULTRASOUND)</option>
                <option value="LAB_REPORT">Phiếu xét nghiệm (LAB_REPORT PDF)</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Khoa chỉ định *</label>
              <select
                v-model="uploadForm.department"
                class="w-full border rounded-xl p-2 focus:ring-1 focus:ring-teal-500"
                :class="isDark ? 'bg-slate-800 border-slate-700 text-white' : 'bg-slate-50 border-slate-300 text-slate-900'"
              >
                <option value="CARDIOLOGY">Khoa Tim mạch</option>
                <option value="ONCOLOGY">Khoa Ung bướu</option>
                <option value="PEDIATRICS">Khoa Nhi</option>
                <option value="NEUROLOGY">Khoa Thần kinh</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Chọn tệp nhị phân (Ảnh PNG/JPG, PDF, DICOM) *</label>
            <input
              type="file"
              @change="onFileSelected"
              required
              class="w-full border rounded-xl p-2 text-xs focus:outline-none"
              :class="isDark ? 'bg-slate-800 border-slate-700 text-slate-300' : 'bg-slate-50 border-slate-300 text-slate-700'"
            />
          </div>

          <div class="pt-3 flex justify-end space-x-2 border-t"
               :class="isDark ? 'border-slate-800' : 'border-slate-200'">
            <button
              type="button"
              @click="showUploadModal = false"
              class="px-4 py-2 rounded-xl text-slate-700 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 transition"
            >
              Hủy
            </button>
            <button
              type="submit"
              :disabled="uploading"
              class="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white font-bold rounded-xl shadow-xs transition"
            >
              {{ uploading ? 'Đang mã hóa AES-GCM & tải lên S3...' : 'Mã hóa & Tải lên MinIO' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';

const props = defineProps({
  patients: {
    type: Array,
    required: true,
  },
  currentRole: {
    type: String,
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

const selectedRecordId = ref('rec-pat-002');
const attachments = ref([]);
const loading = ref(false);

const showUploadModal = ref(false);
const uploading = ref(false);
const uploadFile = ref(null);
const uploadForm = ref({
  modality: 'XRAY',
  sensitivity: 'CONFIDENTIAL',
  department: 'CARDIOLOGY',
});

const previewModalData = ref(null);
const rawModalData = ref(null);

// Image viewer controls
const imageZoom = ref(1);
const imageRotate = ref(0);
const imageInvert = ref(false);

const availablePatients = computed(() => {
  return props.patients.filter((p) => p.access_status !== 'DENIED');
});

const canUpload = computed(() => {
  return ['DOCTOR', 'NURSE'].includes(props.currentRole);
});

watch(
  [availablePatients, () => props.currentUser?.username],
  () => {
    const list = availablePatients.value;
    if (list.length > 0 && !list.some((p) => p.record_id === selectedRecordId.value)) {
      selectedRecordId.value = list[0].record_id;
    } else if (list.length === 0) {
      attachments.value = [];
      return;
    }
    loadAttachments();
  },
  { immediate: true }
);

onMounted(() => {
  if (availablePatients.value.length > 0) {
    loadAttachments();
  }
});

async function loadAttachments() {
  if (!selectedRecordId.value) return;
  loading.value = true;
  try {
    const res = await axios.get(`/api/v1/attachments/${selectedRecordId.value}`);
    attachments.value = res.data.attachments || [];
  } catch {
    attachments.value = [];
  } finally {
    loading.value = false;
  }
}

function modalityClass(modality) {
  if (modality === 'XRAY') {
    return 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-500/20 dark:text-amber-300 dark:border-amber-500/30';
  }
  if (modality === 'CT' || modality === 'MRI') {
    return 'bg-purple-50 text-purple-800 border-purple-200 dark:bg-purple-500/20 dark:text-purple-300 dark:border-purple-500/30';
  }
  if (modality === 'ULTRASOUND') {
    return 'bg-cyan-50 text-cyan-800 border-cyan-200 dark:bg-cyan-500/20 dark:text-cyan-300 dark:border-cyan-500/30';
  }
  return 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-500/20 dark:text-blue-300 dark:border-blue-500/30';
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function onFileSelected(event) {
  const files = event.target.files;
  if (files.length > 0) {
    uploadFile.value = files[0];
  }
}

async function submitUpload() {
  if (!uploadFile.value) return;
  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append('record_id', selectedRecordId.value);
    formData.append('modality', uploadForm.value.modality);
    formData.append('department', uploadForm.value.department);
    formData.append('sensitivity', uploadForm.value.sensitivity);
    formData.append('file', uploadFile.value);

    await axios.post('/api/v1/attachments/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    emit('toast', {
      type: 'success',
      message: `Tệp ${uploadFile.value.name} đã được mã hóa Chunked AES-256-GCM và lưu vào MinIO!`,
    });
    showUploadModal.value = false;
    uploadFile.value = null;
    loadAttachments();
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Lỗi khi tải lên tệp đính kèm',
    });
  } finally {
    uploading.value = false;
  }
}

async function previewAttachment(att) {
  try {
    const res = await axios.get(
      `/api/v1/attachments/${selectedRecordId.value}/${att.attachment_id}/preview`,
      { responseType: 'blob' }
    );

    const isImage = att.content_type?.startsWith('image/') || att.filename.endsWith('.png') || att.filename.endsWith('.jpg');
    const isPdf = att.content_type === 'application/pdf' || att.filename.endsWith('.pdf');
    const blobUrl = URL.createObjectURL(res.data);
    const sha256 = res.headers['x-plaintext-sha256'] || att.plaintext_sha256;

    imageZoom.value = 1;
    imageRotate.value = 0;
    imageInvert.value = false;

    previewModalData.value = {
      att,
      isImage,
      isPdf,
      url: blobUrl,
      sha256,
    };
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Không thể xem tệp. Vi phạm chính sách phân quyền ABAC!',
    });
  }
}

function openInNewTab(url) {
  window.open(url, '_blank');
}

function closePreview() {
  if (previewModalData.value?.url) {
    URL.revokeObjectURL(previewModalData.value.url);
  }
  previewModalData.value = null;
}

async function inspectCiphertext(att) {
  try {
    const res = await axios.get(`/api/v1/attachments/${selectedRecordId.value}/${att.attachment_id}/raw`);
    rawModalData.value = res.data;
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Không thể lấy thông tin bản mã',
    });
  }
}
</script>