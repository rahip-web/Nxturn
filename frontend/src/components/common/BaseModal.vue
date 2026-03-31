<script setup lang="ts">
import { XMarkIcon } from '@heroicons/vue/24/solid'
import { computed, useAttrs } from 'vue'
import type { StyleValue } from 'vue'

// Define props - Combining both versions
const props = defineProps<{
  show: boolean
  title: string
  maxWidth?: string // Aditya's improvement
}>()

const emit = defineEmits(['close'])

// Disable automatic attribute inheritance (Aditya's improvement)
defineOptions({
  inheritAttrs: false,
})

// Get all attributes
const attrs = useAttrs()

// Create a computed property for attributes (Aditya's improvement)
const filteredAttributes = computed(() => {
  const { class: className, style, ...otherAttrs } = attrs
  const result: Record<string, unknown> = { ...otherAttrs }
  if (className) result.class = className
  if (style) result.style = style as StyleValue
  return result
})

// Compute container classes - Merging your critical Flex/Height logic with his width logic
const containerClass = computed(() => {
  // We use YOUR max-h-[90vh] because 70vh is too short for our forms
  const base =
    'relative flex flex-col w-full min-h-0 bg-white/95 backdrop-blur-xl shadow-[0_20px_60px_-20px_rgba(2,6,23,0.45)] border border-sky-200/80 ring-1 ring-sky-500/20 overflow-hidden max-h-[calc(100dvh-2rem)] sm:max-h-[90dvh] rounded-2xl'
  const maxWidthClass =
    props.maxWidth || 'max-w-none sm:max-w-sm md:max-w-md lg:max-w-lg xl:max-w-xl'

  return `${base} ${maxWidthClass}`
})

function closeModal() {
  emit('close')
}
</script>

<template>
  <teleport to="body">
    <!-- Backdrop -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="show"
        class="fixed inset-0 z-40 bg-gradient-to-b from-slate-950/70 via-slate-900/60 to-slate-950/70 backdrop-blur-sm"
        @click="closeModal"
      ></div>
    </transition>

    <!-- Modal -->
    <transition
      enter-active-class="transition ease-out duration-300"
      enter-from-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
      enter-to-class="opacity-100 translate-y-0 sm:scale-100"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100 translate-y-0 sm:scale-100"
      leave-to-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
    >
      <!-- Click container for "click outside" -->
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-2 sm:p-4 md:p-6 pb-[calc(0.5rem+env(safe-area-inset-bottom))] overflow-y-auto"
        @click="closeModal"
      >
        <!-- Modal panel - Using the merged containerClass and filteredAttributes -->
        <div :class="containerClass" v-bind="filteredAttributes" @click.stop>
          <!-- Modal Header (flex-shrink-0 prevents it from disappearing - Your Fix) -->
          <div
            class="flex items-center justify-between gap-3 p-4 sm:p-5 md:p-6 border-b border-slate-200/70 bg-white/80 backdrop-blur flex-shrink-0"
          >
            <h3 class="text-base sm:text-lg md:text-xl font-semibold text-slate-900">
              {{ title }}
            </h3>
            <button
              @click="closeModal"
              class="p-2 rounded-full text-slate-400 hover:bg-slate-100/80 hover:text-slate-700 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
              aria-label="Close modal"
            >
              <XMarkIcon class="w-6 h-6" />
            </button>
          </div>

          <!-- Modal Body (overflow-y-auto enables scrolling - Your Fix) -->
          <div class="p-4 sm:p-6 md:p-7 overflow-y-auto flex-grow min-h-0 text-slate-700">
            <slot></slot>
          </div>

          <!-- Modal Footer (flex-shrink-0 prevents it from disappearing - Your Fix) -->
          <div
            v-if="$slots.footer"
            class="p-4 sm:p-5 bg-slate-50/70 border-t border-slate-200/70 flex-shrink-0"
          >
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>
