<script setup lang="ts">
import { ref, computed } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'vue-toastification'
import { PlusIcon } from '@heroicons/vue/24/solid'
import SkillCategoryCard from '../cards/SkillCategoryCard.vue'
import SkillCategoryForm from '../forms/SkillCategoryForm.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import type { SkillCategory, Skill } from '@/types'

const profileStore = useProfileStore()
const authStore = useAuthStore()
const toast = useToast()

const isOwner = computed(
  () => authStore.currentUser?.username === profileStore.currentProfile?.user.username,
)
const categories = computed(() => profileStore.currentProfile?.skill_categories || [])

// --- Modal State ---
const showAddCategoryModal = ref(false)
const showManageCategoryModal = ref(false)
const activeCategory = ref<SkillCategory | null>(null)
const isSubmitting = ref(false)

// --- Add Category Logic ---
const newCategoryName = ref('')

const openAddCategory = () => {
  newCategoryName.value = ''
  showAddCategoryModal.value = true
}

const handleAddCategory = async () => {
  if (!newCategoryName.value.trim() || !profileStore.currentProfile) return
  isSubmitting.value = true
  try {
    await profileStore.addSkillCategory(
      profileStore.currentProfile.user.username,
      newCategoryName.value,
    )
    toast.success('Category created!')
    showAddCategoryModal.value = false
  } catch (error: any) {
    toast.error(error.message || 'Failed to create category')
  } finally {
    isSubmitting.value = false
  }
}

// --- Manage Category Logic (Edit Skills) ---
const openManageCategory = (category: SkillCategory) => {
  activeCategory.value = category // Note: In a real app, you might want to clone this to avoid reactivity issues
  showManageCategoryModal.value = true
}

const handleDeleteCategory = async (id: number) => {
  if (!confirm('Delete this category and all its skills?')) return
  if (!profileStore.currentProfile) return
  try {
    await profileStore.deleteSkillCategory(profileStore.currentProfile.user.username, id)
    toast.success('Category deleted')
  } catch (error: any) {
    toast.error(error.message)
  }
}

// --- Skill Actions (Inside Category) ---
const handleAddSkill = async (payload: Omit<Skill, 'id'>) => {
  if (!activeCategory.value || !profileStore.currentProfile) return
  isSubmitting.value = true
  try {
    await profileStore.addSkill(
      profileStore.currentProfile.user.username,
      activeCategory.value.id,
      payload,
    )
    toast.success('Skill added!')
  } catch (error: any) {
    toast.error(error.message)
  } finally {
    isSubmitting.value = false
  }
}

const handleDeleteSkill = async (skillId: number) => {
  if (!activeCategory.value || !profileStore.currentProfile) return
  try {
    await profileStore.deleteSkill(
      profileStore.currentProfile.user.username,
      skillId,
      activeCategory.value.id,
    )
    toast.success('Skill removed')
  } catch (error: any) {
    toast.error(error.message)
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header / Add Button -->
    <div class="flex items-start justify-between gap-4 border-b border-slate-200/70 pb-4">
      <div>
        <h3 class="text-lg font-bold text-slate-900">Skills & Expertise</h3>
        <p class="text-sm text-slate-500">
          Group your skills into focused categories for a cleaner profile.
        </p>
      </div>

      <button
        v-if="isOwner"
        @click="openAddCategory"
        class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 shadow-sm transition-colors font-semibold text-sm"
      >
        <PlusIcon class="w-5 h-5" />
        Add Category
      </button>
    </div>

    <!-- Empty State -->
    <div
      v-if="categories.length === 0"
      class="text-center py-12 sm:py-14 bg-gradient-to-br from-slate-50 via-white to-slate-50 rounded-2xl border border-dashed border-slate-200"
    >
      <div
        class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-blue-600"
      >
        <PlusIcon class="h-6 w-6" />
      </div>
      <p class="text-slate-600 font-medium">No skills added yet.</p>
      <p class="text-sm text-slate-400 mt-1">Create a category to get started.</p>
      <button
        v-if="isOwner"
        @click="openAddCategory"
        class="mt-4 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-100 transition-colors"
      >
        <PlusIcon class="w-4 h-4" />
        New Category
      </button>
    </div>

    <!-- Categories Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <SkillCategoryCard
        v-for="cat in categories"
        :key="cat.id"
        :category="cat"
        :is-owner="isOwner"
        @edit="openManageCategory"
        @delete="handleDeleteCategory"
      />
    </div>

    <!-- Modal 1: Create Category -->
    <BaseModal
      :show="showAddCategoryModal"
      title="Create New Category"
      @close="showAddCategoryModal = false"
    >
      <form @submit.prevent="handleAddCategory" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Category Name</label>
          <input
            v-model="newCategoryName"
            type="text"
            placeholder="e.g. Frontend, DevOps, Hobbies"
            class="mt-1 w-full p-2 border border-blue-400 rounded-md outline-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-0 focus:border-blue-500"
            autofocus
          />
        </div>
        <div class="flex justify-end pt-2">
          <button
            type="submit"
            :disabled="!newCategoryName.trim() || isSubmitting"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            Create
          </button>
        </div>
      </form>
    </BaseModal>

    <!-- Modal 2: Manage Category (Add/Remove Skills) -->
    <BaseModal
      :show="showManageCategoryModal"
      :title="activeCategory ? `Manage ${activeCategory.name}` : 'Manage Category'"
      @close="showManageCategoryModal = false"
    >
      <SkillCategoryForm
        v-if="activeCategory"
        :category="activeCategory"
        :is-submitting="isSubmitting"
        @add-skill="handleAddSkill"
        @delete-skill="handleDeleteSkill"
        @close="showManageCategoryModal = false"
      />
    </BaseModal>
  </div>
</template>
