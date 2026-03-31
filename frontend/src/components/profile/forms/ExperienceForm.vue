<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Experience } from '@/types'
import {
  BriefcaseIcon,
  BuildingOffice2Icon,
  MapPinIcon,
  CalendarDaysIcon,
  DocumentTextIcon,
} from '@heroicons/vue/24/solid'

// --- Props & Emits ---
const props = defineProps<{
  initialData?: Experience | null // If null, we are in "Add" mode
  isSubmitting?: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: Omit<Experience, 'id'>): void
  (e: 'cancel'): void
}>()

// --- Constants ---
const MONTHS = [
  { value: '01', label: 'January' },
  { value: '02', label: 'February' },
  { value: '03', label: 'March' },
  { value: '04', label: 'April' },
  { value: '05', label: 'May' },
  { value: '06', label: 'June' },
  { value: '07', label: 'July' },
  { value: '08', label: 'August' },
  { value: '09', label: 'September' },
  { value: '10', label: 'October' },
  { value: '11', label: 'November' },
  { value: '12', label: 'December' },
]

// --- Form State ---
const title = ref('')
const company = ref('')
const location = ref('')
const description = ref('')
const isCurrentRole = ref(false)

// Date State (Split into Month/Year for better UX)
const startMonth = ref('')
const startYear = ref<number | null>(null)
const endMonth = ref('')
const endYear = ref<number | null>(null)

// --- Validation Errors ---
const errors = ref({
  title: '',
  company: '',
  startDate: '',
  endDate: '',
})

// --- Initialize Data ---
onMounted(() => {
  if (props.initialData) {
    title.value = props.initialData.title
    company.value = props.initialData.company
    location.value = props.initialData.location || ''
    description.value = props.initialData.description || ''

    // Parse Start Date
    if (props.initialData.start_date) {
      const [y, m] = props.initialData.start_date.split('-')
      startYear.value = parseInt(y)
      startMonth.value = m
    }

    // Parse End Date
    if (props.initialData.end_date) {
      const [y, m] = props.initialData.end_date.split('-')
      endYear.value = parseInt(y)
      endMonth.value = m
      isCurrentRole.value = false
    } else {
      isCurrentRole.value = true
    }
  }
})

// --- Helper: Format Date for API (YYYY-MM-01) ---
function formatDatePayload(year: number | null, month: string): string {
  if (!year || !month) return ''
  return `${year}-${month}-01`
}

// --- Submit Handler ---
function handleSubmit() {
  // 1. Reset Errors
  errors.value = { title: '', company: '', startDate: '', endDate: '' }
  let isValid = true

  // 2. Validate Required Fields
  if (!title.value.trim()) {
    errors.value.title = 'Job title is required'
    isValid = false
  }
  if (!company.value.trim()) {
    errors.value.company = 'Company name is required'
    isValid = false
  }
  if (!startYear.value || !startMonth.value) {
    errors.value.startDate = 'Start date is required'
    isValid = false
  }

  // 3. Validate End Date Logic
  if (!isCurrentRole.value) {
    if (!endYear.value || !endMonth.value) {
      errors.value.endDate = 'End date is required for past roles'
      isValid = false
    } else {
      // Check if End Date is before Start Date
      const start = new Date(startYear.value!, parseInt(startMonth.value) - 1)
      const end = new Date(endYear.value!, parseInt(endMonth.value) - 1)
      if (end < start) {
        errors.value.endDate = 'End date cannot be before start date'
        isValid = false
      }
    }
  }

  if (!isValid) return

  // 4. Construct Payload
  const payload: Omit<Experience, 'id'> = {
    title: title.value,
    company: company.value,
    location: location.value || null,
    description: description.value || null,
    start_date: formatDatePayload(startYear.value, startMonth.value),
    end_date: isCurrentRole.value ? null : formatDatePayload(endYear.value, endMonth.value),
  }

  emit('submit', payload)
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-5">
    <!-- Job Title -->
    <div class="space-y-2">
      <label class="flex items-center gap-2 text-sm font-semibold text-slate-700">
        <BriefcaseIcon class="h-4 w-4 text-blue-500" />
        Job Title <span class="text-red-500">*</span>
      </label>
      <div class="relative">
        <BriefcaseIcon
          class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
        />
        <input
          v-model="title"
          type="text"
          class="block w-full rounded-lg border border-slate-200 bg-white px-10 py-2.5 text-sm text-slate-800 shadow-sm outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          placeholder="e.g. Senior Software Engineer"
        />
      </div>
      <p v-if="errors.title" class="text-xs text-red-500">{{ errors.title }}</p>
    </div>

    <!-- Company -->
    <div class="space-y-2">
      <label class="flex items-center gap-2 text-sm font-semibold text-slate-700">
        <BuildingOffice2Icon class="h-4 w-4 text-indigo-500" />
        Company Name <span class="text-red-500">*</span>
      </label>
      <div class="relative">
        <BuildingOffice2Icon
          class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
        />
        <input
          v-model="company"
          type="text"
          class="block w-full rounded-lg border border-slate-200 bg-white px-10 py-2.5 text-sm text-slate-800 shadow-sm outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          placeholder="e.g. Microsoft"
        />
      </div>
      <p v-if="errors.company" class="text-xs text-red-500">{{ errors.company }}</p>
    </div>

    <!-- Location -->
    <div class="space-y-2">
      <label class="flex items-center gap-2 text-sm font-semibold text-slate-700">
        <MapPinIcon class="h-4 w-4 text-rose-500" />
        Location
      </label>
      <div class="relative">
        <MapPinIcon
          class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
        />
        <input
          v-model="location"
          type="text"
          class="block w-full rounded-lg border border-slate-200 bg-white px-10 py-2.5 text-sm text-slate-800 shadow-sm outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          placeholder="e.g. Bangalore, India (Optional)"
        />
      </div>
    </div>

    <!-- Checkbox: Current Role -->
    <div class="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-2">
      <input
        id="isCurrent"
        v-model="isCurrentRole"
        type="checkbox"
        class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-200"
      />
      <label for="isCurrent" class="text-sm font-medium text-slate-700 select-none">
        I currently work here
      </label>
    </div>

    <!-- Dates -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div class="space-y-2">
        <label class="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <CalendarDaysIcon class="h-4 w-4 text-orange-500" />
          Start Date <span class="text-red-500">*</span>
        </label>
        <div class="grid grid-cols-2 gap-2">
          <div class="relative">
            <CalendarDaysIcon
              class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            />
            <select
              v-model="startMonth"
              class="block w-full rounded-lg border border-slate-200 bg-white px-9 py-2.5 text-sm text-slate-700 shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option value="" disabled>Month</option>
              <option v-for="m in MONTHS" :key="m.value" :value="m.value">{{ m.label }}</option>
            </select>
          </div>
          <div class="relative">
            <CalendarDaysIcon
              class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            />
            <input
              v-model="startYear"
              type="number"
              placeholder="Year"
              min="1960"
              :max="new Date().getFullYear() + 1"
              class="block w-full rounded-lg border border-slate-200 bg-white px-9 py-2.5 text-sm text-slate-700 shadow-sm outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
        </div>
        <p v-if="errors.startDate" class="text-xs text-red-500">{{ errors.startDate }}</p>
      </div>

      <div v-if="!isCurrentRole" class="space-y-2">
        <label class="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <CalendarDaysIcon class="h-4 w-4 text-teal-500" />
          End Date <span class="text-red-500">*</span>
        </label>
        <div class="grid grid-cols-2 gap-2">
          <div class="relative">
            <CalendarDaysIcon
              class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            />
            <select
              v-model="endMonth"
              class="block w-full rounded-lg border border-slate-200 bg-white px-9 py-2.5 text-sm text-slate-700 shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option value="" disabled>Month</option>
              <option v-for="m in MONTHS" :key="m.value" :value="m.value">{{ m.label }}</option>
            </select>
          </div>
          <div class="relative">
            <CalendarDaysIcon
              class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            />
            <input
              v-model="endYear"
              type="number"
              placeholder="Year"
              min="1960"
              :max="new Date().getFullYear() + 5"
              class="block w-full rounded-lg border border-slate-200 bg-white px-9 py-2.5 text-sm text-slate-700 shadow-sm outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
        </div>
        <p v-if="errors.endDate" class="text-xs text-red-500">{{ errors.endDate }}</p>
      </div>
    </div>

    <!-- Description -->
    <div class="space-y-2">
      <label class="flex items-center gap-2 text-sm font-semibold text-slate-700">
        <DocumentTextIcon class="h-4 w-4 text-amber-500" />
        Description
      </label>
      <div class="relative">
        <DocumentTextIcon
          class="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-slate-400"
        />
        <textarea
          v-model="description"
          rows="5"
          class="block w-full rounded-lg border border-slate-200 bg-white px-10 py-2.5 text-sm text-slate-700 shadow-sm outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 max-h-[10.5rem] overflow-y-auto resize-none"
          placeholder="Describe your role, responsibilities, and achievements..."
        ></textarea>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end">
      <button
        type="button"
        @click="emit('cancel')"
        class="inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-200"
      >
        Cancel
      </button>
      <button
        type="submit"
        :disabled="isSubmitting"
        class="inline-flex items-center justify-center rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {{ isSubmitting ? 'Saving...' : 'Save' }}
      </button>
    </div>
  </form>
</template>
