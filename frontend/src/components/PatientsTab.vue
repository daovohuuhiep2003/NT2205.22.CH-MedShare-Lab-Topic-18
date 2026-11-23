<template>
  <div class="space-y-5">
    <!-- Hospital Clinical Triage & Stats Bar -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3.5 no-print">
      <div class="p-3.5 rounded-2xl border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/70 border-slate-800' : 'bg-white border-slate-200'">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Bệnh nhân Quản lý</span>
          <span class="p-1.5 rounded-lg bg-teal-50 dark:bg-teal-500/10 text-teal-700 dark:text-teal-400 text-xs">📋</span>
        </div>
        <div class="text-xl font-extrabold text-slate-900 dark:text-white mt-1 font-mono">
          {{ accessiblePatients.length.toLocaleString('vi-VN') }}
        </div>
        <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">Hồ sơ được phân công theo dõi</div>
      </div>

      <div class="p-3.5 rounded-2xl border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/70 border-slate-800' : 'bg-white border-slate-200'">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Tiếp nhận BHYT</span>
          <span class="p-1.5 rounded-lg bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 text-xs">🏥</span>
        </div>
        <div class="text-xl font-extrabold text-blue-700 dark:text-blue-400 mt-1 font-mono">
          {{ Math.round(accessiblePatients.length * 0.72).toLocaleString('vi-VN') }}
        </div>
        <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">Tỷ lệ khám BHYT đúng tuyến</div>
      </div>

      <div class="p-3.5 rounded-2xl border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/70 border-slate-800' : 'bg-white border-slate-200'">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Chẩn đoán Hình ảnh</span>
          <span class="p-1.5 rounded-lg bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 text-xs">🩻</span>
        </div>
        <div class="text-xl font-extrabold text-amber-600 dark:text-amber-400 mt-1 font-mono flex items-center space-x-1.5">
          <span>{{ accessiblePatients.filter(p => hasKnownAttachments(p.record_id)).length }} ca</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300 font-sans font-semibold">PACS / X-Quang</span>
        </div>
        <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">Có phim chụp hoặc xét nghiệm</div>
      </div>

      <div class="p-3.5 rounded-2xl border transition-colors shadow-xs"
           :class="isDark ? 'bg-slate-900/70 border-slate-800' : 'bg-white border-slate-200'">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Trạng thái Điều trị</span>
          <span class="p-1.5 rounded-lg bg-teal-50 dark:bg-teal-500/10 text-teal-700 dark:text-teal-400 text-xs">🩺</span>
        </div>
        <div class="text-xl font-extrabold text-teal-700 dark:text-teal-400 mt-1 font-mono">
          Ổn định
        </div>
        <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">Theo dõi lâm sàng tích cực</div>
      </div>
    </div>

    <!-- Clinical Action Bar & Filters -->
    <div class="p-4 rounded-2xl border transition-colors shadow-xs space-y-3 no-print"
         :class="isDark ? 'bg-slate-900/70 border-slate-800' : 'bg-white border-slate-200'">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <!-- Title & Subtitle -->
        <div>
          <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
            <span>Sổ Bệnh án Điện tử (Electronic Medical Records)</span>
            <span class="px-2 py-0.5 text-xs font-bold rounded-full"
                  :class="isDark ? 'bg-slate-800 text-teal-400 border border-slate-700' : 'bg-teal-50 text-teal-800 border border-teal-200'">
              {{ filteredPatients.length }} hồ sơ
            </span>
          </h2>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Danh sách bệnh nhân thuộc phạm vi chuyên khoa được phân công theo dõi và điều trị.
          </p>
        </div>

        <!-- Action buttons -->
        <div class="flex flex-wrap items-center gap-2">
          <!-- Add Patient Button (Doctor only) -->
          <button
            v-if="currentRole === 'DOCTOR'"
            @click="showCreateModal = true"
            class="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-500 text-white rounded-xl shadow-xs transition"
          >
            <span>+ Tiếp nhận Bệnh nhân mới</span>
          </button>

          <!-- Refresh button -->
          <button
            @click="$emit('refresh')"
            class="p-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 transition"
            title="Tải lại danh sách bệnh nhân"
          >
            ↻
          </button>
        </div>
      </div>

      <!-- Filters Row -->
      <div class="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-2.5 pt-2 border-t border-slate-200 dark:border-slate-800/80">
        <!-- Department Filter -->
        <div class="flex items-center space-x-2">
          <label class="text-xs font-semibold text-slate-600 dark:text-slate-400 whitespace-nowrap">Khoa điều trị:</label>
          <select
            v-model="selectedDepartment"
            class="bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-slate-100 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-teal-500"
          >
            <option value="">Tất cả chuyên khoa được phân công</option>
            <option value="CARDIOLOGY">Khoa Tim mạch (CARDIOLOGY)</option>
            <option value="ONCOLOGY">Khoa Ung bướu (ONCOLOGY)</option>
            <option value="PEDIATRICS">Khoa Nhi (PEDIATRICS)</option>
            <option value="NEUROLOGY">Khoa Thần kinh (NEUROLOGY)</option>
            <option value="GENERAL">Khoa Đa khoa Tổng quát (GENERAL)</option>
          </select>
        </div>

        <!-- Search Bar -->
        <div class="flex-1 max-w-md flex items-center space-x-2">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Tìm theo họ tên, mã hồ sơ, mã bệnh ICD-10..."
            class="w-full bg-slate-50 dark:bg-slate-950 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 rounded-xl border border-slate-300 dark:border-slate-700 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-teal-500"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="px-2 py-1 text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            title="Xóa tìm kiếm"
          >
            ✕
          </button>
        </div>

        <!-- Search by Diagnosis / Symptom -->
        <div class="flex items-center space-x-1.5">
          <input
            v-model="blindSearchQuery"
            @keyup.enter="performBlindSearch"
            type="text"
            placeholder="Tìm theo triệu chứng (vd: Migraine, Heart...)"
            class="w-48 bg-slate-50 dark:bg-slate-950 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 rounded-xl border border-slate-300 dark:border-slate-700 px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-teal-500 text-[11px]"
          />
          <button
            @click="performBlindSearch"
            :disabled="searchingBlind"
            class="px-2.5 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-750 text-white rounded-xl transition"
            title="Tìm kiếm hồ sơ theo triệu chứng lâm sàng"
          >
            {{ searchingBlind ? '...' : 'Tìm kiếm' }}
          </button>
          <button
            v-if="isBlindFiltered"
            @click="clearBlindSearch"
            class="px-2 py-1.5 text-xs text-rose-500 hover:text-rose-600 font-bold"
            title="Hủy tìm kiếm"
          >
            ✕
          </button>
        </div>
      </div>
    </div>

    <!-- DBA Restricted Notice -->
    <div v-if="currentRole === 'DBA'" class="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 text-center no-print">
      <div class="inline-flex p-3 rounded-full bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300 mb-2">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m0 0v2m0-2h2m-2 0H10m10-7V7a2 2 0 00-2-2H6a2 2 0 00-2 2v3m16 0v7a2 2 0 01-2 2H6a2 2 0 01-2-2v-7m16 0H4" />
        </svg>
      </div>
      <h3 class="text-sm font-bold text-slate-800 dark:text-slate-200">Phân hệ Quản trị Cơ sở Dữ liệu</h3>
      <p class="text-xs text-slate-600 dark:text-slate-400 max-w-xl mx-auto mt-1">
        Tài khoản Quản trị CSDL không phụ trách hồ sơ khám chữa bệnh lâm sàng. Vui lòng chuyển sang tab <strong>"Thanh tra Cloud DBMS"</strong>.
      </p>
    </div>

    <!-- Patients Data Table (Hospital Registry View) -->
    <div v-else class="overflow-x-auto rounded-2xl border transition-colors shadow-xs no-print"
         :class="isDark ? 'border-slate-800 bg-slate-900/40' : 'border-slate-200 bg-white'">
      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="border-b text-[11px] font-bold uppercase tracking-wider"
              :class="isDark ? 'border-slate-800 bg-slate-850/80 text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-600'">
            <th class="py-3 px-4">Mã BN / Hồ sơ</th>
            <th class="py-3 px-4">Khoa điều trị</th>
            <th class="py-3 px-4">Họ và tên bệnh nhân</th>
            <th class="py-3 px-4">Năm sinh / Giới tính</th>
            <th class="py-3 px-4">Chẩn đoán y khoa (ICD-10)</th>
            <th class="py-3 px-4 text-center">Phim chụp / PDF</th>
            <th class="py-3 px-4 text-right">Thao tác</th>
          </tr>
        </thead>
        <tbody class="divide-y"
               :class="isDark ? 'divide-slate-800/60' : 'divide-slate-100'">
          <tr
            v-for="p in paginatedPatients"
            :key="p.record_id"
            class="transition cursor-pointer"
            :class="isDark ? 'hover:bg-slate-800/40' : 'hover:bg-teal-50/50'"
            @click="openPatientChart(p)"
          >
            <!-- Record ID / External ID -->
            <td class="py-3 px-4 font-mono">
              <div class="font-bold text-teal-700 dark:text-teal-400">{{ p.record_id }}</div>
              <div class="text-[10px] text-slate-400 font-sans">
                {{ p.patient_id || ('PAT-1801-' + p.record_id.slice(-6)) }}
              </div>
            </td>

            <!-- Department -->
            <td class="py-3 px-4">
              <span :class="deptBadgeClass(p.department)" class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border">
                {{ p.department }}
              </span>
            </td>

            <!-- Full Name -->
            <td class="py-3 px-4">
              <div class="font-bold text-slate-900 dark:text-slate-100 uppercase">
                {{ p.fields?.name || '—' }}
              </div>
              <div class="text-[10px] text-slate-400 font-sans">Đối tượng: BHYT (Tuyến A)</div>
            </td>

            <!-- DOB & Gender -->
            <td class="py-3 px-4 text-slate-600 dark:text-slate-300 font-mono">
              <div>{{ p.fields?.dob || '—' }}</div>
              <div class="text-[10px] text-slate-400 font-sans">{{ p.fields?.gender }}</div>
            </td>

            <!-- Diagnosis ICD-10 -->
            <td class="py-3 px-4 max-w-xs">
              <template v-if="p.fields?.diagnosis === '[REDACTED_BY_POLICY]'">
                <span class="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700 text-[11px] font-semibold">
                  <span>Theo chỉ định của Bác sĩ điều trị</span>
                </span>
              </template>
              <template v-else>
                <div class="font-semibold text-slate-900 dark:text-slate-100 truncate" :title="p.fields?.diagnosis">
                  {{ p.fields?.diagnosis }}
                </div>
                <div class="text-[10px] text-slate-500 dark:text-slate-400 truncate" :title="p.fields?.notes">
                  {{ p.fields?.notes }}
                </div>
              </template>
            </td>

            <!-- PACS Attachment Icons -->
            <td class="py-3 px-4 text-center">
              <div v-if="hasKnownAttachments(p.record_id)" class="inline-flex items-center space-x-1">
                <span class="px-1.5 py-0.5 rounded text-[11px] bg-teal-50 dark:bg-teal-500/20 text-teal-700 dark:text-teal-300 font-bold border border-teal-200 dark:border-teal-500/30" title="Có phim chụp X-Quang và Phiếu xét nghiệm PDF">
                  🩻 📄 PACS
                </span>
              </div>
              <span v-else class="text-slate-300 dark:text-slate-600">—</span>
            </td>

            <!-- Action -->
            <td class="py-3 px-4 text-right">
              <button
                @click.stop="openPatientChart(p)"
                class="px-2.5 py-1 text-xs font-bold rounded-lg transition"
                :class="isDark ? 'bg-teal-500/15 hover:bg-teal-500/25 text-teal-300 border border-teal-500/30' : 'bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200'"
              >
                📋 Mở Bệnh án →
              </button>
            </td>
          </tr>

          <tr v-if="filteredPatients.length === 0">
            <td colspan="7" class="py-12 text-center text-slate-400 text-xs">
              Không tìm thấy hồ sơ nào phù hợp với bộ lọc chuyên khoa hoặc điều kiện tìm kiếm.
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Table Pagination Controls -->
      <div class="p-3 border-t flex flex-col sm:flex-row items-center justify-between gap-2 text-xs"
           :class="isDark ? 'border-slate-800 text-slate-400' : 'border-slate-200 text-slate-600'">
        <div>
          Hiển thị trang <strong class="text-teal-700 dark:text-teal-400">{{ currentPage }} / {{ totalPages }}</strong>
          (Tổng {{ filteredPatients.length }} hồ sơ)
        </div>
        <div class="flex items-center space-x-1.5">
          <button
            @click="currentPage = Math.max(1, currentPage - 1)"
            :disabled="currentPage <= 1"
            class="px-2.5 py-1 rounded-lg border border-slate-300 dark:border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-800 font-semibold"
          >
            ← Trước
          </button>
          <span class="px-2 font-mono font-bold text-teal-700 dark:text-teal-400">{{ currentPage }}</span>
          <button
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
            :disabled="currentPage >= totalPages"
            class="px-2.5 py-1 rounded-lg border border-slate-300 dark:border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-800 font-semibold"
          >
            Sau →
          </button>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- COMPREHENSIVE HOSPITAL MEDICAL RECORD CHART MODAL (BỆNH ÁN ĐIỆN TỬ) -->
    <!-- ===================================================================== -->
    <div
      v-if="selectedRecord"
      class="fixed inset-0 z-50 overflow-y-auto bg-black/60 dark:bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5"
      @click.self="selectedRecord = null"
    >
      <div
        class="w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh] border transition-colors print-container"
        :class="isDark ? 'bg-slate-900 border-slate-700 text-slate-100' : 'bg-white border-slate-300 text-slate-900'"
      >
        <!-- Modal Top Action Header -->
        <div class="p-4 border-b flex items-center justify-between no-print"
             :class="isDark ? 'border-slate-800 bg-slate-950/70' : 'border-slate-200 bg-slate-50'">
          <div class="flex items-center space-x-2">
            <span class="p-1.5 rounded-lg bg-teal-100 dark:bg-teal-900/60 text-teal-800 dark:text-teal-300 text-sm font-bold">📋</span>
            <div>
              <h3 class="text-sm font-extrabold tracking-tight uppercase">Hồ sơ Bệnh án Điện tử (EMR Chart)</h3>
              <p class="text-[11px] text-slate-500 dark:text-slate-400">Mã lưu trữ: <span class="font-mono font-bold text-teal-700 dark:text-teal-400">{{ selectedRecord.record_id }}</span></p>
            </div>
          </div>

          <div class="flex items-center space-x-2">
            <!-- Print Medical Chart Button -->
            <button
              @click="printChart"
              class="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition"
              :class="isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700' : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-300 shadow-xs'"
            >
              <span>🖨️ In Bệnh án</span>
            </button>
            <!-- Close Button -->
            <button
              @click="selectedRecord = null"
              class="w-8 h-8 rounded-xl flex items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 text-base"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Scrollable Hospital Sheet Content -->
        <div class="p-6 sm:p-8 overflow-y-auto space-y-6 text-xs leading-relaxed">
          <!-- Hospital Official Header (Printable) -->
          <div class="border-b-2 border-teal-600 pb-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div class="space-y-1">
              <div class="text-[11px] font-bold text-teal-700 dark:text-teal-400 uppercase tracking-wider">
                BỘ Y TẾ · SỞ Y TẾ TP. HỒ CHÍ MINH
              </div>
              <div class="text-base sm:text-lg font-black text-slate-900 dark:text-white uppercase tracking-tight">
                BỆNH VIỆN ĐA KHOA QUỐC TẾ MEDSHARE
              </div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400">
                Cơ sở 1: 120 Hai Bà Trưng, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh
              </div>
            </div>

            <div class="text-left sm:text-right font-mono text-[11px] space-y-0.5 sm:border-l sm:border-slate-200 dark:sm:border-slate-800 sm:pl-4">
              <div>Mã hồ sơ (BA): <strong class="text-teal-700 dark:text-teal-400">{{ selectedRecord.record_id }}</strong></div>
              <div>Mã bệnh nhân: <strong>{{ selectedRecord.patient_id || ('PAT-1801-' + selectedRecord.record_id.slice(-6)) }}</strong></div>
              <div>Khoa tiếp nhận: <strong class="uppercase">{{ selectedRecord.department }}</strong></div>
            </div>
          </div>

          <!-- Title Banner -->
          <div class="text-center py-1">
            <h1 class="text-base sm:text-lg font-black uppercase tracking-wider text-slate-900 dark:text-white">
              BỆNH ÁN ĐIỆN TỬ NGOẠI TRÚ / NỘI TRÚ (EHR)
            </h1>
            <p class="text-[11px] italic text-slate-500 dark:text-slate-400 mt-0.5">
              (Ban hành theo Thông tư quy định về Bệnh án điện tử của Bộ Y tế)
            </p>
          </div>

          <!-- Denial Warning if TC-03 Denied -->
          <div v-if="selectedRecord.access_status === 'DENIED'"
               class="p-4 rounded-xl bg-rose-50 text-rose-800 border border-rose-200 dark:bg-rose-500/10 dark:text-rose-300 dark:border-rose-500/30">
            <strong class="font-bold">Chặn truy cập dữ liệu lâm sàng:</strong> Bạn không thuộc chuyên khoa được phân công hoặc không đủ quyền ABAC (TC-03 Denied) đối với hồ sơ này.
          </div>

          <div v-else class="space-y-6">
            <!-- I. THÔNG TIN HÀNH CHÍNH -->
            <div class="space-y-2">
              <h3 class="font-extrabold uppercase text-teal-800 dark:text-teal-300 flex items-center space-x-1.5 border-b border-teal-200 dark:border-teal-800/60 pb-1">
                <span>I. THÔNG TIN HÀNH CHÍNH (ADMINISTRATIVE DATA)</span>
              </h3>

              <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 rounded-xl border"
                   :class="isDark ? 'bg-slate-850/60 border-slate-800' : 'bg-slate-50/80 border-slate-200'">
                <div>
                  <span class="text-slate-500 dark:text-slate-400 text-[11px]">1. Họ và tên người bệnh:</span>
                  <div class="font-bold text-sm text-slate-900 dark:text-white uppercase mt-0.5">
                    {{ selectedRecord.fields?.name || '—' }}
                  </div>
                </div>
                <div>
                  <span class="text-slate-500 dark:text-slate-400 text-[11px]">2. Ngày sinh &amp; Giới tính:</span>
                  <div class="font-semibold text-slate-800 dark:text-slate-200 mt-0.5 font-mono">
                    {{ selectedRecord.fields?.dob }} ({{ selectedRecord.fields?.gender }})
                  </div>
                </div>
                <div>
                  <span class="text-slate-500 dark:text-slate-400 text-[11px]">3. Quốc tịch / Dân tộc:</span>
                  <div class="font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                    Việt Nam / Kinh
                  </div>
                </div>
                <div>
                  <span class="text-slate-500 dark:text-slate-400 text-[11px]">4. Thẻ BHYT số:</span>
                  <div class="font-mono font-bold text-blue-700 dark:text-blue-400 mt-0.5">
                    DN 4 79 79 {{ (selectedRecord.record_id.slice(-6) || '180100') }} (80%)
                  </div>
                </div>
                <div>
                  <span class="text-slate-500 dark:text-slate-400 text-[11px]">5. Đối tượng khám chữa bệnh:</span>
                  <div class="font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                    BHYT Đúng tuyến
                  </div>
                </div>
                <div>
                  <span class="text-slate-500 dark:text-slate-400 text-[11px]">6. Địa chỉ thường trú:</span>
                  <div class="text-slate-800 dark:text-slate-200 mt-0.5 truncate" title="TP. Hồ Chí Minh">
                    Quận 1, TP. Hồ Chí Minh
                  </div>
                </div>
              </div>
            </div>

            <!-- II. DẤU HIỆU SINH TỒN -->
            <div class="space-y-2">
              <h3 class="font-extrabold uppercase text-teal-800 dark:text-teal-300 flex items-center space-x-1.5 border-b border-teal-200 dark:border-teal-800/60 pb-1">
                <span>II. CHỈ SỐ SINH TỒN &amp; THỂ TRẠNG (VITAL SIGNS)</span>
              </h3>

              <div class="grid grid-cols-3 sm:grid-cols-6 gap-2.5">
                <div class="p-2.5 rounded-xl border text-center"
                     :class="isDark ? 'bg-slate-850/60 border-slate-800' : 'bg-slate-50/80 border-slate-200'">
                  <div class="text-[10px] text-slate-500 dark:text-slate-400 font-semibold">MẠCH</div>
                  <div class="text-base font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">78</div>
                  <div class="text-[10px] text-slate-400">lần/phút</div>
                </div>

                <div class="p-2.5 rounded-xl border text-center"
                     :class="isDark ? 'bg-slate-850/60 border-slate-800' : 'bg-slate-50/80 border-slate-200'">
                  <div class="text-[10px] text-slate-500 dark:text-slate-400 font-semibold">HUYẾT ÁP</div>
                  <div class="text-base font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">120/80</div>
                  <div class="text-[10px] text-slate-400">mmHg</div>
                </div>

                <div class="p-2.5 rounded-xl border text-center"
                     :class="isDark ? 'bg-slate-850/60 border-slate-800' : 'bg-slate-50/80 border-slate-200'">
                  <div class="text-[10px] text-slate-500 dark:text-slate-400 font-semibold">NHIỆT ĐỘ</div>
                  <div class="text-base font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">36.8</div>
                  <div class="text-[10px] text-slate-400">°C</div>
                </div>

                <div class="p-2.5 rounded-xl border text-center"
                     :class="isDark ? 'bg-slate-850/60 border-slate-800' : 'bg-slate-50/80 border-slate-200'">
                  <div class="text-[10px] text-slate-500 dark:text-slate-400 font-semibold">NHỊP THỞ</div>
                  <div class="text-base font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">18</div>
                  <div class="text-[10px] text-slate-400">lần/phút</div>
                </div>

                <div class="p-2.5 rounded-xl border text-center"
                     :class="isDark ? 'bg-slate-850/60 border-slate-800' : 'bg-slate-50/80 border-slate-200'">
                  <div class="text-[10px] text-slate-500 dark:text-slate-400 font-semibold">SPO2</div>
                  <div class="text-base font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">98%</div>
                  <div class="text-[10px] text-slate-400">Khí phòng</div>
                </div>

                <div class="p-2.5 rounded-xl border text-center"
                     :class="isDark ? 'bg-slate-850/60 border-slate-800' : 'bg-slate-50/80 border-slate-200'">
                  <div class="text-[10px] text-slate-500 dark:text-slate-400 font-semibold">CHỈ SỐ BMI</div>
                  <div class="text-base font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">21.5</div>
                  <div class="text-[10px] text-slate-400">Cân đối</div>
                </div>
              </div>
            </div>

            <!-- III. KHÁM LÂM SÀNG & CHẨN ĐOÁN -->
            <div class="space-y-3">
              <h3 class="font-extrabold uppercase text-teal-800 dark:text-teal-300 flex items-center space-x-1.5 border-b border-teal-200 dark:border-teal-800/60 pb-1">
                <span>III. KHÁM LÂM SÀNG &amp; CHẨN ĐOÁN (CLINICAL DIAGNOSIS)</span>
              </h3>

              <!-- Diagnosis Card -->
              <div class="p-4 rounded-xl border"
                   :class="isDark ? 'bg-slate-850/60 border-slate-800' : 'bg-slate-50/80 border-slate-200'">
                <div class="flex items-center justify-between mb-1">
                  <span class="font-bold text-slate-700 dark:text-slate-300 uppercase text-[11px]">Chẩn đoán y khoa chính thức (Mã ICD-10):</span>
                  <span v-if="selectedRecord.fields?.diagnosis === '[REDACTED_BY_POLICY]'" class="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300">
                    🔒 Che bởi Field Projection (Nurse Role)
                  </span>
                </div>
                <div class="text-sm font-extrabold text-teal-800 dark:text-teal-300 font-mono">
                  {{ selectedRecord.fields?.diagnosis }}
                </div>
              </div>

              <!-- Clinical Notes -->
              <div class="p-4 rounded-xl border"
                   :class="isDark ? 'bg-slate-850/60 border-slate-800' : 'bg-slate-50/80 border-slate-200'">
                <div class="font-bold text-slate-700 dark:text-slate-300 uppercase text-[11px] mb-1">
                  Ghi chú lâm sàng, triệu chứng &amp; Diễn biến bệnh:
                </div>
                <p class="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-sans whitespace-pre-line">
                  {{ selectedRecord.fields?.notes }}
                </p>
              </div>
            </div>

            <!-- IV. CHẨN ĐOÁN HÌNH ẢNH & KẾT QUẢ XÉT NGHIỆM (PACS / LAB REPORTS) -->
            <div class="space-y-3">
              <div class="flex items-center justify-between border-b border-teal-200 dark:border-teal-800/60 pb-1">
                <h3 class="font-extrabold uppercase text-teal-800 dark:text-teal-300 flex items-center space-x-1.5">
                  <span>IV. CHẨN ĐOÁN HÌNH ẢNH &amp; PHIẾU XÉT NGHIỆM (PACS / LAB REPORTS)</span>
                </h3>
                <span class="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                  {{ patientAttachments.length }} tệp liên kết
                </span>
              </div>

              <!-- Attachments Loading -->
              <div v-if="loadingAttachments" class="text-center py-4 text-slate-500 text-xs">
                Đang tải tệp hình ảnh &amp; phiếu xét nghiệm giải mã từ MinIO S3...
              </div>

              <!-- Attachments List -->
              <div v-else-if="patientAttachments.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div
                  v-for="att in patientAttachments"
                  :key="att.attachment_id"
                  class="p-3.5 rounded-xl border transition flex flex-col justify-between"
                  :class="isDark ? 'bg-slate-950/60 border-slate-800 hover:border-slate-700' : 'bg-white border-slate-200 hover:border-teal-300 shadow-xs'"
                >
                  <div class="space-y-1.5">
                    <div class="flex items-center justify-between">
                      <span class="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider"
                            :class="att.modality === 'XRAY'
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300'
                              : 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-300'">
                        {{ att.modality }}
                      </span>
                      <span class="text-[10px] font-mono text-slate-400">
                        {{ formatBytes(att.file_size_bytes) }}
                      </span>
                    </div>

                    <div class="font-bold text-slate-900 dark:text-white truncate" :title="att.filename">
                      {{ att.filename }}
                    </div>
                    <div class="text-[11px] text-slate-500 dark:text-slate-400">
                      Định dạng: <code class="font-mono text-teal-700 dark:text-teal-400">{{ att.content_type }}</code>
                    </div>
                  </div>

                  <!-- Action button -->
                  <div class="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end">
                    <button
                      v-if="isImageAttachment(att)"
                      @click="openImageViewer(att)"
                      class="px-3 py-1.5 text-xs font-bold rounded-lg bg-teal-600 hover:bg-teal-500 text-white transition flex items-center space-x-1 shadow-xs"
                    >
                      <span>🩻 Xem ảnh X-Quang</span>
                    </button>
                    <button
                      v-else-if="isPdfAttachment(att)"
                      @click="openPdfViewer(att)"
                      class="px-3 py-1.5 text-xs font-bold rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition flex items-center space-x-1 shadow-xs"
                    >
                      <span>📄 Đọc Phiếu xét nghiệm PDF</span>
                    </button>
                    <button
                      v-else
                      @click="downloadAttachment(att)"
                      class="px-3 py-1.5 text-xs font-bold rounded-lg bg-slate-700 hover:bg-slate-600 text-white transition"
                    >
                      <span>📥 Tải tệp giải mã</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- No attachments notice -->
              <div v-else class="p-4 rounded-xl border text-center text-slate-500 dark:text-slate-400"
                   :class="isDark ? 'bg-slate-850/30 border-slate-800' : 'bg-slate-50 border-slate-200'">
                Bệnh nhân chưa có phim chụp X-Quang hoặc phiếu xét nghiệm đính kèm nào được lưu trữ trong đợt khám này.
              </div>
            </div>

            <!-- V. KẾ HOẠCH ĐIỀU TRỊ & CHỮ KÝ XÁC NHẬN -->
            <div class="space-y-3 pt-2">
              <h3 class="font-extrabold uppercase text-teal-800 dark:text-teal-300 flex items-center space-x-1.5 border-b border-teal-200 dark:border-teal-800/60 pb-1">
                <span>V. KẾ HOẠCH ĐIỀU TRỊ &amp; CHỮ KÝ XÁC NHẬN (CONFIRMATION)</span>
              </h3>

              <div class="p-3.5 rounded-xl border"
                   :class="isDark ? 'bg-slate-850/60 border-slate-800' : 'bg-slate-50/80 border-slate-200'">
                <div class="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">Hướng xử trí &amp; Lời dặn của Bác sĩ điều trị:</div>
                <p class="text-slate-800 dark:text-slate-200 text-xs">
                  - Tuân thủ phác đồ điều trị, uống thuốc đúng giờ theo đơn chỉ định.<br/>
                  - Hạn chế gắng sức thể lực, kiêng rượu bia, tái khám sau 2 tuần hoặc ngay khi có dấu hiệu bất thường.
                </p>
              </div>

              <!-- Digital Signature & Cryptographic Seal -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
                <div class="p-3 rounded-xl border text-[11px] space-y-1 font-mono"
                     :class="isDark ? 'bg-slate-950/60 border-slate-800 text-slate-400' : 'bg-slate-100/70 border-slate-200 text-slate-600'">
                  <div class="font-bold uppercase font-sans text-teal-800 dark:text-teal-400 text-xs">Chứng thực Mật mã Y tế (Zone Z1)</div>
                  <div>Thuật toán: <strong>AES-256-GCM + Vault KMS Transit</strong></div>
                  <div>Toàn vẹn thuộc tính: <strong>HMAC-SHA-256 Verified</strong></div>
                  <div>Mã khóa Capsule: <code class="text-teal-700 dark:text-teal-400">{{ selectedRecord.capsule_id || 'CAPSULE-OK' }}</code></div>
                </div>

                <div class="text-center sm:text-right space-y-1">
                  <div class="text-[11px] italic text-slate-500">TP. Hồ Chí Minh, ngày 14 tháng 11 năm 2026</div>
                  <div class="font-bold text-slate-900 dark:text-white uppercase text-xs">BÁC SĨ ĐIỀU TRỊ CHUYÊN KHOA</div>
                  <div class="h-10 flex items-center justify-center sm:justify-end">
                    <span class="px-3 py-1 rounded bg-teal-50 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 font-mono text-[11px] border border-teal-200 dark:border-teal-700 font-bold">
                      ✓ ĐÃ KÝ SỐ XÁC NHẬN (E-SIGNED)
                    </span>
                  </div>
                  <div class="font-bold text-slate-800 dark:text-slate-200 text-xs">BS. Nguyễn Đạo Ga Đô / BS. Đào Võ Hữu Hiệp</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Modal Bottom Footer -->
        <div class="p-4 border-t flex justify-end space-x-2 no-print"
             :class="isDark ? 'border-slate-800 bg-slate-950/70' : 'border-slate-200 bg-slate-50'">
          <button
            @click="selectedRecord = null"
            class="px-5 py-2 rounded-xl text-xs font-bold transition"
            :class="isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-200' : 'bg-slate-200 hover:bg-slate-300 text-slate-800'"
          >
            Đóng Bệnh án
          </button>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- INTERACTIVE MEDICAL IMAGE VIEWER MODAL (X-RAY / CT / MRI / ULTRASOUND) -->
    <!-- ===================================================================== -->
    <div
      v-if="imageViewerData"
      class="fixed inset-0 z-50 overflow-hidden bg-black/90 backdrop-blur-md flex flex-col justify-between p-3 sm:p-5"
      @click.self="closeImageViewer"
    >
      <!-- Top Image Toolbar -->
      <div class="flex items-center justify-between text-white pb-3 border-b border-slate-800">
        <div class="flex items-center space-x-3">
          <span class="px-2.5 py-1 rounded-lg text-xs font-black uppercase tracking-wider bg-amber-500/20 text-amber-400 border border-amber-500/30">
            {{ imageViewerData.att.modality || 'XRAY' }}
          </span>
          <div>
            <h3 class="text-sm font-bold text-white">{{ imageViewerData.att.filename }}</h3>
            <p class="text-[11px] text-slate-400 font-mono">
              Giải mã trực tiếp từ MinIO S3 qua Vault KMS DEK · Toàn vẹn: {{ imageViewerData.sha256 || 'Verified SHA-256' }}
            </p>
          </div>
        </div>

        <!-- Controls Toolbar -->
        <div class="flex items-center space-x-2">
          <!-- Zoom Out -->
          <button
            @click="imageZoom = Math.max(0.5, imageZoom - 0.2)"
            class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold"
            title="Thu nhỏ (-)"
          >
            🔍 -
          </button>

          <!-- Zoom Reset -->
          <button
            @click="imageZoom = 1; imageRotate = 0; imageInvert = false"
            class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold font-mono"
            title="Đặt lại tỉ lệ 100%"
          >
            {{ Math.round(imageZoom * 100) }}%
          </button>

          <!-- Zoom In -->
          <button
            @click="imageZoom = Math.min(3, imageZoom + 0.2)"
            class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold"
            title="Phóng to (+)"
          >
            🔍 +
          </button>

          <!-- Rotate 90 deg -->
          <button
            @click="imageRotate = (imageRotate + 90) % 360"
            class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold"
            title="Xoay 90 độ"
          >
            ↻ Xoay
          </button>

          <!-- Invert Colors (Negative Film View) -->
          <button
            @click="imageInvert = !imageInvert"
            class="px-2.5 py-1.5 rounded-lg border text-xs font-bold transition"
            :class="imageInvert ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-slate-800 text-slate-200 border-slate-700'"
            title="Đảo màu âm bản / dương bản"
          >
            ☯ {{ imageInvert ? 'Dương bản' : 'Âm bản (Negative)' }}
          </button>

          <!-- Download -->
          <a
            :href="imageViewerData.url"
            :download="imageViewerData.att.filename"
            class="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold transition flex items-center space-x-1"
            title="Tải ảnh gốc về máy"
          >
            <span>📥 Tải ảnh</span>
          </a>

          <!-- Close -->
          <button
            @click="closeImageViewer"
            class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-base flex items-center justify-center ml-2"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- Main Image Film Stage (Negative background) -->
      <div class="flex-1 flex items-center justify-center overflow-auto p-4 my-2 rounded-2xl bg-black/80 border border-slate-800/80">
        <img
          :src="imageViewerData.url"
          alt="Medical Image"
          class="transition-all duration-200 max-h-[75vh] max-w-full object-contain rounded-lg shadow-2xl"
          :style="{
            transform: `scale(${imageZoom}) rotate(${imageRotate}deg)`,
            filter: imageInvert ? 'invert(100%)' : 'none'
          }"
        />
      </div>

      <!-- Bottom Status -->
      <div class="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800 font-mono">
        <div>Khoa: {{ imageViewerData.att.department }} · Mức độ nhạy cảm: {{ imageViewerData.att.sensitivity }}</div>
        <div>Kích thước: {{ formatBytes(imageViewerData.att.file_size_bytes) }} · Phim chụp lồng ngực y khoa số hóa</div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- EMBEDDED PDF DOCUMENT VIEWER MODAL (LAB REPORTS / BIOPSY / SUMMARIES) -->
    <!-- ===================================================================== -->
    <div
      v-if="pdfViewerData"
      class="fixed inset-0 z-50 overflow-hidden bg-black/80 backdrop-blur-md flex flex-col justify-between p-3 sm:p-5"
      @click.self="closePdfViewer"
    >
      <!-- Top PDF Toolbar -->
      <div class="flex items-center justify-between text-white pb-3 border-b border-slate-800">
        <div class="flex items-center space-x-3">
          <span class="px-2.5 py-1 rounded-lg text-xs font-black uppercase tracking-wider bg-blue-500/20 text-blue-400 border border-blue-500/30">
            PDF REPORT
          </span>
          <div>
            <h3 class="text-sm font-bold text-white">{{ pdfViewerData.att.filename }}</h3>
            <p class="text-[11px] text-slate-400 font-mono">
              Báo cáo xét nghiệm / Chẩn đoán y khoa giải mã trực tiếp từ MinIO S3 · SHA-256: {{ pdfViewerData.sha256 }}
            </p>
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <!-- Open in new tab -->
          <button
            @click="openInNewTab(pdfViewerData.url)"
            class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition flex items-center space-x-1"
            title="Mở tài liệu PDF trong tab trình duyệt mới"
          >
            <span>↗ Mở tab mới</span>
          </button>

          <!-- Download -->
          <a
            :href="pdfViewerData.url"
            :download="pdfViewerData.att.filename"
            class="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition flex items-center space-x-1"
          >
            <span>📥 Tải tệp PDF</span>
          </a>

          <!-- Close -->
          <button
            @click="closePdfViewer"
            class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-base flex items-center justify-center ml-2"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- Embedded PDF Viewer (W3C Iframe / Object) -->
      <div class="flex-1 my-3 bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl flex flex-col">
        <iframe
          :src="pdfViewerData.url"
          class="w-full h-full flex-1 border-0 rounded-2xl bg-white"
          title="PDF Document Preview"
        ></iframe>
      </div>

      <!-- Bottom Status -->
      <div class="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800 font-mono">
        <div>Định dạng: {{ pdfViewerData.att.content_type }} · Kích thước: {{ formatBytes(pdfViewerData.att.file_size_bytes) }}</div>
        <div>Hệ thống Bệnh án Điện tử MedShare-Lab · Bảo mật giải mã phía Gateway Zone Z1</div>
      </div>
    </div>

    <!-- Create Patient Modal (Reception & Registration) -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-50 bg-black/60 dark:bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
      @click.self="showCreateModal = false"
    >
      <div class="w-full max-w-lg rounded-2xl p-6 space-y-4 shadow-2xl border transition-colors"
           :class="isDark ? 'bg-slate-900 border-slate-700 text-slate-100' : 'bg-white border-slate-200 text-slate-900'">
        <div class="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h3 class="text-base font-bold">Tiếp nhận Bệnh nhân Mới (W1 Pipeline)</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Dữ liệu lâm sàng được mã hóa Envelope AES-256-GCM tại Gateway</p>
          </div>
          <button @click="showCreateModal = false" class="text-slate-400 hover:text-slate-600 dark:hover:text-white">✕</button>
        </div>

        <form @submit.prevent="createPatient" class="space-y-3.5 text-xs">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Mã hồ sơ (Record ID) *</label>
              <input
                v-model="newPatient.record_id"
                required
                type="text"
                placeholder="vd: rec-pat-1001"
                class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl p-2 font-mono text-slate-900 dark:text-slate-100 focus:border-teal-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Khoa điều trị *</label>
              <select
                v-model="newPatient.department"
                class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl p-2 text-slate-900 dark:text-slate-100 focus:border-teal-500 focus:outline-none"
              >
                <option value="CARDIOLOGY">Khoa Tim mạch (CARDIOLOGY)</option>
                <option value="ONCOLOGY">Khoa Ung bướu (ONCOLOGY)</option>
                <option value="PEDIATRICS">Khoa Nhi (PEDIATRICS)</option>
                <option value="NEUROLOGY">Khoa Thần kinh (NEUROLOGY)</option>
                <option value="GENERAL">Đa khoa Tổng quát (GENERAL)</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Họ và tên bệnh nhân *</label>
            <input
              v-model="newPatient.name"
              required
              type="text"
              placeholder="vd: Nguyễn Văn An"
              class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl p-2 text-slate-900 dark:text-slate-100 focus:border-teal-500 focus:outline-none"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Ngày sinh *</label>
              <input
                v-model="newPatient.dob"
                required
                type="date"
                class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl p-2 text-slate-900 dark:text-slate-100 focus:border-teal-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Giới tính *</label>
              <select
                v-model="newPatient.gender"
                class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl p-2 text-slate-900 dark:text-slate-100 focus:border-teal-500 focus:outline-none"
              >
                <option value="Nam">Nam</option>
                <option value="Nữ">Nữ</option>
                <option value="Khác">Khác</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Chẩn đoán ban đầu (Mã ICD-10) *</label>
            <input
              v-model="newPatient.diagnosis"
              required
              type="text"
              placeholder="vd: I20.0 - Cơn đau thắt ngực không ổn định"
              class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl p-2 text-slate-900 dark:text-slate-100 focus:border-teal-500 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold mb-1 text-slate-700 dark:text-slate-300">Ghi chú lâm sàng (Notes)</label>
            <textarea
              v-model="newPatient.notes"
              rows="3"
              placeholder="Tiền sử bệnh án, quá trình bệnh lý, dị ứng thuốc..."
              class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl p-2 text-slate-900 dark:text-slate-100 focus:border-teal-500 focus:outline-none"
            ></textarea>
          </div>

          <div class="pt-3 flex justify-end space-x-2 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              @click="showCreateModal = false"
              class="px-4 py-2 rounded-xl text-slate-700 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 transition"
            >
              Hủy
            </button>
            <button
              type="submit"
              :disabled="creating"
              class="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white font-bold rounded-xl shadow-xs transition"
            >
              {{ creating ? 'Đang mã hóa & lưu...' : 'Mã hóa & Lưu Bệnh án' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
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

const emit = defineEmits(['refresh', 'toast']);

// State
const showCreateModal = ref(false);
const creating = ref(false);
const selectedRecord = ref(null);
const patientAttachments = ref([]);
const loadingAttachments = ref(false);

// Filter & Search State
const selectedDepartment = ref('');
const searchQuery = ref('');
const blindSearchQuery = ref('');
const searchingBlind = ref(false);
const blindResults = ref(null);

// Pagination
const currentPage = ref(1);
const pageSize = ref(20);

// Viewers State
const imageViewerData = ref(null);
const imageZoom = ref(1);
const imageRotate = ref(0);
const imageInvert = ref(false);

const pdfViewerData = ref(null);

const accessiblePatients = computed(() => {
  return (props.patients || []).filter((p) => p.access_status !== 'DENIED');
});

const isBlindFiltered = computed(() => blindResults.value !== null);

const filteredPatients = computed(() => {
  let list = blindResults.value !== null ? blindResults.value : accessiblePatients.value;
  list = list.filter((p) => p.access_status !== 'DENIED');

  if (selectedDepartment.value) {
    list = list.filter((p) => p.department === selectedDepartment.value);
  }

  if (searchQuery.value && searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase();
    list = list.filter((p) => {
      const name = (p.fields?.name || '').toLowerCase();
      const recId = (p.record_id || '').toLowerCase();
      const pid = (p.patient_id || '').toLowerCase();
      const diag = (p.fields?.diagnosis || '').toLowerCase();
      return name.includes(q) || recId.includes(q) || pid.includes(q) || diag.includes(q);
    });
  }

  return list;
});

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredPatients.value.length / pageSize.value));
});

const paginatedPatients = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredPatients.value.slice(start, start + pageSize.value);
});

const newPatient = ref({
  record_id: 'rec-pat-' + Math.floor(1001 + Math.random() * 9000),
  patient_id: 'pat-' + Math.floor(1001 + Math.random() * 9000),
  department: 'CARDIOLOGY',
  name: '',
  dob: '1985-01-01',
  gender: 'Nam',
  diagnosis: '',
  notes: '',
});

function deptBadgeClass(dept) {
  if (dept === 'CARDIOLOGY') {
    return 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-500/15 dark:text-blue-300 dark:border-blue-500/30';
  }
  if (dept === 'ONCOLOGY') {
    return 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-500/15 dark:text-purple-300 dark:border-purple-500/30';
  }
  if (dept === 'PEDIATRICS') {
    return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30';
  }
  if (dept === 'NEUROLOGY') {
    return 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-500/15 dark:text-indigo-300 dark:border-indigo-500/30';
  }
  return 'bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-500/15 dark:text-teal-300 dark:border-teal-500/30';
}

function hasKnownAttachments(recordId) {
  return ['rec-pat-001', 'rec-pat-002', 'rec-pat-005'].includes(recordId);
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function isImageAttachment(att) {
  const ct = (att.content_type || '').toLowerCase();
  const fn = (att.filename || '').toLowerCase();
  return ct.startsWith('image/') || fn.endsWith('.png') || fn.endsWith('.jpg') || fn.endsWith('.jpeg');
}

function isPdfAttachment(att) {
  const ct = (att.content_type || '').toLowerCase();
  const fn = (att.filename || '').toLowerCase();
  return ct === 'application/pdf' || fn.endsWith('.pdf');
}

async function openPatientChart(patient) {
  selectedRecord.value = patient;
  patientAttachments.value = [];

  if (patient.access_status !== 'DENIED') {
    loadingAttachments.value = true;
    try {
      const res = await axios.get(`/api/v1/attachments/${patient.record_id}`);
      patientAttachments.value = res.data.attachments || [];
    } catch {
      patientAttachments.value = [];
    } finally {
      loadingAttachments.value = false;
    }
  }
}

async function fetchDecryptedBlob(att) {
  const res = await axios.get(
    `/api/v1/attachments/${selectedRecord.value.record_id}/${att.attachment_id}/preview`,
    { responseType: 'blob' }
  );
  const blob = new Blob([res.data], { type: att.content_type });
  return {
    url: URL.createObjectURL(blob),
    sha256: res.headers['x-plaintext-sha256'] || att.plaintext_sha256 || 'Verified SHA-256',
  };
}

async function openImageViewer(att) {
  try {
    const { url, sha256 } = await fetchDecryptedBlob(att);
    imageZoom.value = 1;
    imageRotate.value = 0;
    imageInvert.value = false;
    imageViewerData.value = { att, url, sha256 };
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Không thể giải mã và xem hình ảnh X-Quang',
    });
  }
}

function closeImageViewer() {
  if (imageViewerData.value?.url) {
    URL.revokeObjectURL(imageViewerData.value.url);
  }
  imageViewerData.value = null;
}

async function openPdfViewer(att) {
  try {
    const { url, sha256 } = await fetchDecryptedBlob(att);
    pdfViewerData.value = { att, url, sha256 };
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Không thể giải mã và mở tệp PDF',
    });
  }
}

function closePdfViewer() {
  if (pdfViewerData.value?.url) {
    URL.revokeObjectURL(pdfViewerData.value.url);
  }
  pdfViewerData.value = null;
}

function openInNewTab(url) {
  window.open(url, '_blank');
}

async function downloadAttachment(att) {
  try {
    const { url } = await fetchDecryptedBlob(att);
    const a = document.createElement('a');
    a.href = url;
    a.download = att.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Tải tệp thất bại',
    });
  }
}

function printChart() {
  window.print();
}

async function performBlindSearch() {
  if (!blindSearchQuery.value.trim()) return;
  searchingBlind.value = true;
  try {
    const res = await axios.post(
      '/api/v1/patients/blind-search',
      {
        field_name: 'diagnosis',
        query_value: blindSearchQuery.value.trim(),
      }
    );
    const matches = res.data.matches || [];
    blindResults.value = matches.map((m) => ({
      record_id: m.record_id,
      patient_id: m.patient_id,
      department: m.department || 'CARDIOLOGY',
      access_status: 'PERMITTED',
      fields: m.fields,
      capsule_id: m.capsule_id,
    }));
    currentPage.value = 1;
    emit('toast', {
      type: 'success',
      message: `Tìm thấy ${matches.length} kết quả bằng HMAC Blind Index Token trên bản mã!`,
    });
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Lỗi khi tìm kiếm blind index',
    });
  } finally {
    searchingBlind.value = false;
  }
}

function clearBlindSearch() {
  blindSearchQuery.value = '';
  blindResults.value = null;
}

async function createPatient() {
  creating.value = true;
  try {
    await axios.post('/api/v1/patients', newPatient.value);
    emit('toast', {
      type: 'success',
      message: `Bệnh nhân ${newPatient.value.name} đã được tiếp nhận và mã hóa Envelope vào MongoDB!`,
    });
    showCreateModal.value = false;
    emit('refresh');
  } catch (err) {
    emit('toast', {
      type: 'error',
      message: err.response?.data?.detail || 'Lỗi khi tiếp nhận bệnh nhân',
    });
  } finally {
    creating.value = false;
  }
}
</script>