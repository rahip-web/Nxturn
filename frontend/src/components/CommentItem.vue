<script setup lang="ts">
import { getAvatarUrl } from '@/utils/avatars'
import { computed, ref, watch, nextTick } from 'vue'
import { format } from 'date-fns'
import { debounce } from 'lodash-es'
import type { Comment } from '@/stores/comment'
import { useAuthStore } from '@/stores/auth'
import { useCommentStore } from '@/stores/comment'
import axiosInstance from '@/services/axiosInstance'
import MentionAutocomplete from './MentionAutocomplete.vue'

// Font Awesome Icons
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
  faEllipsisVertical,
  faHeart,
  faReply,
  faPenToSquare,
  faTrash,
  faFlag,
  faPaperPlane,
  faRepeat,
  faXmark,
  faChevronDown,
  faChevronUp,
  faImage,
  faFaceLaughBeam,
} from '@fortawesome/free-solid-svg-icons'

const props = defineProps<{
  comment: Comment
  parentPostType: string
  parentObjectId: number
  parentPostActualId: number
  currentDepth?: number
  hideDate?: boolean
}>()

const emit = defineEmits<{
  (
    e: 'report-content',
    payload: { content_type: string; content_type_id: number; object_id: number },
  ): void
}>()

const MAX_REPLY_DEPTH = 1
const effectiveDepth = computed(() => props.currentDepth ?? 0)

const authStore = useAuthStore()
const commentStore = useCommentStore()

const isEditing = ref(false)
const editableContent = ref('')
const showReplyForm = ref(false)
const replyContent = ref('')
const replyInputRef = ref<HTMLTextAreaElement | null>(null)
const isReplyMultiline = ref(false)
const isSubmittingReply = ref(false)
const replyError = ref<string | null>(null)
const showOptionsMenu = ref(false)
const optionsMenuRef = ref<HTMLDivElement | null>(null)
const showReplies = ref(false)
const showMentionDropdown = ref(false)
const mentionSearchResults = ref<
  Array<{ id: number; username: string; first_name: string; last_name: string; picture: string }>
>([])
const mentionIsLoading = ref(false)
const mentionActiveIndex = ref(-1)
const showMentionList = computed(
  () =>
    showMentionDropdown.value && (mentionIsLoading.value || mentionSearchResults.value.length > 0),
)

const isCommentAuthor = computed(() => authStore.currentUser?.id === props.comment.author.id)
const canReplyToThisComment = computed(() => effectiveDepth.value < MAX_REPLY_DEPTH)
const directReplies = computed(() => {
  const postKey = `${props.parentPostType}_${props.parentObjectId}`
  return (commentStore.commentsByPost[postKey] || []).filter(
    (reply) => reply.parent === props.comment.id,
  )
})

// Fix comment count - ensure it's always a number
const commentLikeCount = computed(() => {
  const count = props.comment.like_count
  return typeof count === 'number' ? count : 0
})

const replyCount = computed(() => directReplies.value.length)

function handleReportClick() {
  if (typeof props.comment.comment_content_type_id !== 'number') return

  emit('report-content', {
    content_type: 'comment',
    content_type_id: props.comment.comment_content_type_id,
    object_id: props.comment.id,
  })
  showOptionsMenu.value = false
}

function toggleOptionsMenu() {
  showOptionsMenu.value = !showOptionsMenu.value
}

function handleEditClick() {
  toggleEditMode(true)
  showOptionsMenu.value = false
}

function handleDeleteClick() {
  deleteComment()
  showOptionsMenu.value = false
}

function toggleReplies() {
  showReplies.value = !showReplies.value
}

// Close options menu when clicking outside
const closeOnClickOutside = (event: MouseEvent) => {
  if (optionsMenuRef.value && !optionsMenuRef.value.contains(event.target as Node)) {
    showOptionsMenu.value = false
  }
}

watch(showOptionsMenu, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', closeOnClickOutside, true)
  } else {
    document.removeEventListener('click', closeOnClickOutside, true)
  }
})

function linkifyContent(text: string): string {
  if (!text) return ''
  const urlRegex =
    /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])|(\bwww\.[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gi
  const mentionRegex = /@(\w+)/g
  let linkedText = text.replace(
    urlRegex,
    (url) =>
      `<a href="${url.startsWith('www.') ? 'http://' + url : url}" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:underline break-all">${url}</a>`,
  )
  linkedText = linkedText.replace(mentionRegex, (match, username) => {
    const profileUrl = `/profile/${username}`
    return `<a href="${profileUrl}" class="font-semibold text-blue-600 hover:underline break-all">${match}</a>`
  })
  return linkedText
}

function toggleEditMode(edit: boolean) {
  isEditing.value = edit
  if (edit) {
    showReplyForm.value = false
    editableContent.value = props.comment.content
    nextTick(() => {
      // Focus the edit textarea with safer access
      const textarea = document.querySelector(
        `[data-comment-edit="${props.comment.id}"]`,
      ) as HTMLTextAreaElement
      if (textarea && textarea.value) {
        textarea.focus()
        textarea.setSelectionRange(textarea.value.length, textarea.value.length)
      } else if (textarea) {
        // If textarea exists but value might be empty, still focus it
        textarea.focus()
      }
    })
  }
}

function toggleReplyForm() {
  if (!showReplyForm.value && !canReplyToThisComment.value) {
    return alert(`Replies are limited to ${MAX_REPLY_DEPTH} level(s).`)
  }
  const nextState = !showReplyForm.value
  showReplyForm.value = nextState
  if (showReplyForm.value) {
    isEditing.value = false
    replyContent.value = ''
    replyError.value = null
    resetMentionState()
    nextTick(() => {
      autoResizeReply()
      replyInputRef.value?.focus()
    })
  } else {
    replyContent.value = ''
    replyError.value = null
    resetMentionState()
    autoResizeReply()
  }
}

async function saveEdit() {
  if (!editableContent.value.trim() || editableContent.value.trim() === props.comment.content) {
    return toggleEditMode(false)
  }
  await commentStore.editComment(
    props.comment.id,
    editableContent.value,
    props.parentPostType,
    props.parentObjectId,
  )
  toggleEditMode(false)
}

async function deleteComment() {
  if (window.confirm('Are you sure you want to delete this comment?')) {
    await commentStore.deleteComment(
      props.comment.id,
      props.parentPostType,
      props.parentObjectId,
      props.parentPostActualId,
    )
  }
}

async function submitReply() {
  if (!replyContent.value.trim()) {
    return (replyError.value = 'Reply cannot be empty.')
  }
  isSubmittingReply.value = true
  replyError.value = null
  try {
    await commentStore.createComment(
      props.parentPostType,
      props.parentObjectId,
      replyContent.value,
      props.parentPostActualId,
      props.comment.id,
    )
    toggleReplyForm()
    // Auto-show replies if there are any after adding a new reply
    if (directReplies.value.length > 0) {
      showReplies.value = true
    }
  } catch (error: any) {
    replyError.value = error.message || 'Failed to submit reply.'
  } finally {
    isSubmittingReply.value = false
  }
}

async function handleToggleCommentLike() {
  if (!authStore.isAuthenticated) return alert('Please log in to like comments.')
  if (typeof props.comment.comment_content_type_id !== 'number') return
  await commentStore.toggleLikeOnComment(
    props.comment.id,
    props.comment.comment_content_type_id,
    props.parentPostType,
    props.parentObjectId,
  )
}

// Watch for mention dropdown changes
watch(showMentionDropdown, (isOpen) => {
  if (!isOpen) {
    mentionSearchResults.value = []
    mentionActiveIndex.value = -1
  }
})

function resetMentionState() {
  showMentionDropdown.value = false
  mentionSearchResults.value = []
  mentionActiveIndex.value = -1
  mentionIsLoading.value = false
  searchMentionUsers.cancel?.()
}

// Mention autocomplete functions
const searchMentionUsers = debounce(async (query: string) => {
  if (query.length < 1) {
    mentionSearchResults.value = []
    return
  }
  mentionIsLoading.value = true
  try {
    const response = await axiosInstance.get('/search/users/', {
      params: { q: query, page_size: 5 },
    })
    mentionSearchResults.value = response.data.results
  } catch (error) {
    console.error('Failed to search for users:', error)
    mentionSearchResults.value = []
  } finally {
    mentionIsLoading.value = false
  }
}, 300)

function checkForMentionInReply(text: string, cursorPosition: number) {
  const textBeforeCursor = text.slice(0, cursorPosition)
  const mentionMatch = textBeforeCursor.match(/@([\w.-]*)$/)

  if (mentionMatch) {
    showMentionDropdown.value = true
    mentionActiveIndex.value = -1
    searchMentionUsers(mentionMatch[1])
  } else {
    showMentionDropdown.value = false
  }
}

function autoResizeReply() {
  const el = replyInputRef.value
  if (!el) return
  el.style.height = 'auto'
  const maxHeight = 96
  el.style.height = Math.min(el.scrollHeight, maxHeight) + 'px'
  isReplyMultiline.value = el.scrollHeight > 44
}

function handleReplyInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  replyContent.value = target.value
  autoResizeReply()
  checkForMentionInReply(target.value, target.selectionStart || 0)
}

function selectMentionUser(user: any) {
  const inputElement = replyInputRef.value
  if (!inputElement) return

  const currentText = replyContent.value
  const cursorPosition = inputElement.selectionStart || 0
  const textBeforeCursor = currentText.slice(0, cursorPosition)
  const mentionStartIndex = textBeforeCursor.lastIndexOf('@')

  if (mentionStartIndex !== -1) {
    const textBeforeMention = currentText.slice(0, mentionStartIndex)
    const textAfterCursor = currentText.slice(cursorPosition)
    const newText = `${textBeforeMention}@${user.username} ${textAfterCursor}`
    replyContent.value = newText
    const newCursorPosition = (textBeforeMention + `@${user.username} `).length

    nextTick(() => {
      inputElement.focus()
      inputElement.setSelectionRange(newCursorPosition, newCursorPosition)
    })
  }

  showMentionDropdown.value = false
}

function handleMentionKeydown(event: KeyboardEvent) {
  if (!showMentionDropdown.value || mentionSearchResults.value.length === 0) return

  if (event.key === 'ArrowDown') {
    event.preventDefault()
    mentionActiveIndex.value = (mentionActiveIndex.value + 1) % mentionSearchResults.value.length
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    mentionActiveIndex.value =
      (mentionActiveIndex.value - 1 + mentionSearchResults.value.length) %
      mentionSearchResults.value.length
  } else if (event.key === 'Enter' && mentionActiveIndex.value !== -1) {
    event.preventDefault()
    selectMentionUser(mentionSearchResults.value[mentionActiveIndex.value])
  } else if (event.key === 'Escape') {
    event.preventDefault()
    showMentionDropdown.value = false
  }
}

// GIF functionality placeholder
function handleGifClick() {
  console.log('GIF picker would open here')
  alert('GIF functionality would be implemented here with a GIF picker')
}

// Emoji functionality placeholder
function handleEmojiClick() {
  console.log('Emoji picker would open here')
  alert('Emoji functionality would be implemented here with an emoji picker')
}
</script>

<template>
  <div
    class="flex items-start gap-2 py-2 border-b border-gray-100 last:border-b-0 transition-all duration-200 hover:bg-gray-50/50 px-1 rounded-lg group"
    :class="{ 'bg-blue-50/30': showReplies }"
  >
    <!-- Avatar -->
    <div class="flex-shrink-0">
      <img
        :src="
          getAvatarUrl(comment.author.picture, comment.author.first_name, comment.author.last_name)
        "
        alt="comment author avatar"
        class="w-7 h-7 sm:w-8 sm:h-8 rounded-full object-cover bg-gradient-to-br from-blue-50 to-gray-100 border border-gray-200 shadow-sm"
      />
    </div>

    <div class="flex-grow min-w-0">
      <!-- Comment Card -->
      <div
        class="bg-white rounded-lg p-2 sm:p-3 border border-gray-100 shadow-sm transition-all duration-200 hover:shadow-md relative"
      >
        <!-- Header with author, date, and options menu -->
        <div class="flex items-center justify-between mb-1">
          <div class="flex items-center gap-1 flex-wrap">
            <span class="font-semibold text-xs sm:text-sm text-gray-900 tracking-tight">{{
              props.comment.author.username
            }}</span>
            <!-- Date - Hidden on mobile, shown on larger screens -->
            <span
              v-if="!hideDate"
              class="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded-full hidden sm:inline"
            >
              {{ format(new Date(props.comment.created_at), 'MMM d, yyyy') }}
            </span>
            <!-- Time - Always shown -->
            <span class="text-xs text-gray-400">
              {{ format(new Date(props.comment.created_at), 'h:mm a') }}
            </span>
          </div>

          <!-- Three Dots Options Menu - Always Visible -->
          <div v-if="authStore.isAuthenticated" class="relative" ref="optionsMenuRef">
            <button
              @click.stop="toggleOptionsMenu"
              class="w-5 h-5 flex items-center justify-center rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors duration-200 border border-gray-300 bg-white shadow-sm"
            >
              <FontAwesomeIcon :icon="faEllipsisVertical" class="w-3 h-3" />
            </button>

            <div
              v-if="showOptionsMenu"
              class="absolute right-0 top-6 mt-1 w-32 rounded-lg shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10 border border-gray-200 py-1"
            >
              <!-- Edit Option (Author only) -->
              <button
                v-if="isCommentAuthor"
                @click="handleEditClick"
                class="w-full text-left flex items-center px-2 py-1.5 text-sm text-gray-700 hover:bg-green-50 transition-colors duration-200 group"
              >
                <FontAwesomeIcon
                  :icon="faPenToSquare"
                  class="w-3 h-3 mr-1.5 text-green-500 group-hover:text-green-600"
                />
                <span class="text-xs group-hover:text-green-600">Edit</span>
              </button>

              <!-- Delete Option (Author only) -->
              <button
                v-if="isCommentAuthor"
                @click="handleDeleteClick"
                class="w-full text-left flex items-center px-2 py-1.5 text-sm text-red-700 hover:bg-red-50 transition-colors duration-200 group"
              >
                <FontAwesomeIcon
                  :icon="faTrash"
                  class="w-3 h-3 mr-1.5 text-red-500 group-hover:text-red-600"
                />
                <span class="text-xs group-hover:text-red-600">Delete</span>
              </button>

              <!-- Report Option (Non-author only) -->
              <button
                v-if="!isCommentAuthor"
                @click="handleReportClick"
                class="w-full text-left flex items-center px-2 py-1.5 text-sm text-orange-700 hover:bg-orange-50 transition-colors duration-200 group"
              >
                <FontAwesomeIcon
                  :icon="faFlag"
                  class="w-3 h-3 mr-1.5 text-orange-500 group-hover:text-orange-600"
                />
                <span class="text-xs group-hover:text-orange-600">Report</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Comment Content with improved word breaking -->
        <div
          v-if="!isEditing"
          class="text-xs sm:text-sm text-gray-800 leading-relaxed whitespace-pre-wrap break-words overflow-hidden"
          style="word-wrap: break-word; overflow-wrap: break-word; hyphens: auto"
        >
          <span v-html="linkifyContent(props.comment.content)"></span>
        </div>

        <!-- Edit Form -->
        <form v-else @submit.prevent="saveEdit" class="mt-1">
          <MentionAutocomplete
            :data-comment-edit="comment.id"
            v-model="editableContent"
            placeholder="Edit your comment..."
            :rows="2"
            class="text-xs sm:text-sm w-full border border-gray-300 rounded-lg px-2 py-1.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          />
          <div class="flex justify-end gap-1.5 mt-2">
            <button
              @click="toggleEditMode(false)"
              type="button"
              class="flex items-center gap-1 text-xs font-medium text-gray-600 px-2 py-1.5 rounded-lg hover:bg-gray-100 transition-colors duration-150 border border-gray-300"
            >
              <FontAwesomeIcon :icon="faXmark" class="w-3 h-3" />
              Cancel
            </button>
            <button
              type="submit"
              class="flex items-center gap-1 text-xs font-medium text-white bg-gradient-to-r from-blue-500 to-blue-600 px-2 py-1.5 rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all duration-200 shadow-sm"
            >
              <FontAwesomeIcon :icon="faPenToSquare" class="w-3 h-3" />
              Save
            </button>
          </div>
        </form>
      </div>

      <!-- Action Buttons -->
      <div v-if="!isEditing" class="flex items-center gap-1.5 mt-2 px-0.5 flex-wrap">
        <!-- Like Button -->
        <button
          @click="handleToggleCommentLike"
          class="flex items-center gap-1 text-xs font-medium px-1.5 py-1 rounded-lg transition-all duration-200"
          :class="
            props.comment.is_liked_by_user
              ? 'text-red-500 bg-red-50 hover:bg-red-100'
              : 'text-gray-600 bg-gray-50 hover:bg-gray-100'
          "
        >
          <FontAwesomeIcon
            :icon="faHeart"
            class="w-3 h-3"
            :class="props.comment.is_liked_by_user ? 'fill-current' : ''"
          />
          Like ({{ commentLikeCount }})
        </button>

        <!-- Reply Button -->
        <button
          v-if="canReplyToThisComment"
          @click="toggleReplyForm"
          class="flex items-center gap-1 text-xs font-medium text-gray-600 bg-gray-50 hover:bg-gray-100 px-1.5 py-1 rounded-lg transition-all duration-200"
        >
          <FontAwesomeIcon :icon="faReply" class="w-3 h-3" />
          Reply
        </button>

        <!-- Replies Toggle Button -->
        <button
          v-if="replyCount > 0"
          @click="toggleReplies"
          class="flex items-center gap-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 px-1.5 py-1 rounded-lg transition-all duration-200 ml-auto"
        >
          <FontAwesomeIcon
            :icon="showReplies ? faChevronUp : faChevronDown"
            class="w-3 h-3 transition-transform duration-200"
          />
          <span class="hidden sm:inline">{{ showReplies ? 'Hide' : 'Show' }} Replies</span>
          <span class="sm:ml-1">({{ replyCount }})</span>
        </button>
      </div>

      <!-- Reply Form -->
      <div v-if="showReplyForm" class="mt-2">
        <form
          @submit.prevent="submitReply"
          class="flex items-center gap-2 px-2.5 sm:px-3 py-2 bg-white border border-gray-100 rounded-full overflow-visible"
        >
          <img
            :src="
              getAvatarUrl(
                authStore.currentUser?.picture,
                authStore.currentUser?.first_name,
                authStore.currentUser?.last_name,
              )
            "
            alt="your avatar"
            class="w-6 h-6 sm:w-7 sm:h-7 rounded-full object-cover flex-shrink-0 bg-gray-200"
          />

          <div class="relative flex-1 overflow-visible">
            <textarea
              ref="replyInputRef"
              :value="replyContent"
              rows="1"
              placeholder="Write a reply..."
              :data-comment-reply-input="comment.id"
              @keydown="handleMentionKeydown"
              @input="handleReplyInput"
              :class="[
                'w-full text-sm sm:text-base px-4 py-2 sm:py-2.5 pr-12 sm:pr-24 bg-gray-100 border border-transparent focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none overflow-y-auto leading-4 sm:leading-5 transition-colors rounded-xl',
                isReplyMultiline ? 'rounded-2xl' : 'rounded-xl',
              ]"
            ></textarea>

            <!-- Mention Dropdown -->
            <div
              v-show="showMentionList"
              data-mention-dropdown
              class="absolute left-0 right-0 top-full mt-2 w-full bg-white border border-gray-200 rounded-lg shadow-lg z-30 max-h-56 overflow-y-auto"
            >
              <div v-if="mentionIsLoading" class="px-4 py-3 text-sm text-gray-500 text-center">
                <div class="inline-block">Searching...</div>
              </div>
              <div
                v-else-if="mentionSearchResults.length === 0"
                class="px-4 py-3 text-sm text-gray-500 text-center"
              >
                No users found.
              </div>
              <div v-else>
                <button
                  v-for="(user, index) in mentionSearchResults"
                  :key="user.id"
                  type="button"
                  @click="selectMentionUser(user)"
                  class="w-full flex items-center gap-3 px-4 py-3 hover:bg-blue-50 transition-colors border-b border-gray-100 last:border-b-0 text-left"
                  :class="{ 'bg-blue-100': index === mentionActiveIndex }"
                >
                  <img
                    :src="getAvatarUrl(user.picture, user.first_name, user.last_name)"
                    alt="user avatar"
                    class="w-8 h-8 rounded-full object-cover flex-shrink-0"
                  />
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-gray-900 text-sm">{{ user.username }}</div>
                    <div class="text-xs text-gray-500">
                      {{ user.first_name }} {{ user.last_name }}
                    </div>
                  </div>
                </button>
              </div>
            </div>

            <div class="absolute right-3 top-1/2 -translate-y-1/2 hidden sm:flex items-center gap-2">
              <!-- <button
                type="button"
                @click="handleGifClick"
                class="text-purple-600 hover:text-purple-700 flex items-center justify-center transition-colors duration-150"
                title="Add GIF"
              >
                <span class="text-[10px] font-bold leading-none">GIF</span>
              </button> -->

              <!-- <button
                type="button"
                @click="handleEmojiClick"
                class="text-yellow-500 hover:text-yellow-600 flex items-center justify-center transition-colors duration-150"
                title="Add emoji"
              >
                <FontAwesomeIcon :icon="faFaceLaughBeam" class="w-4 h-4" />
              </button> -->
            </div>
          </div>

          <button
            type="submit"
            :disabled="isSubmittingReply || !replyContent.trim()"
            class="text-blue-600 hover:text-blue-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center"
            title="Send reply"
          >
            <FontAwesomeIcon :icon="faPaperPlane" class="w-4 h-4" />
          </button>

          <button
            type="button"
            @click="toggleReplyForm"
            class="text-gray-500 hover:text-gray-700 flex items-center justify-center"
            title="Cancel"
          >
            <FontAwesomeIcon :icon="faXmark" class="w-4 h-4" />
          </button>
        </form>

        <div v-if="showMentionList" class="h-56 mt-2"></div>

        <div
          v-if="replyError"
          class="text-red-500 text-xs mt-2 font-medium bg-red-50 px-3 py-2 rounded-lg border border-red-100"
        >
          {{ replyError }}
        </div>
      </div>

      <!-- Nested Replies -->
      <div
        v-if="directReplies.length > 0 && showReplies"
        class="mt-3 ml-0 sm:ml-1 pl-2 sm:pl-3 border-l-2 border-blue-200 space-y-2 max-h-64 overflow-y-auto"
      >
        <CommentItem
          v-for="reply in directReplies"
          :key="reply.id"
          :comment="reply"
          :parentPostType="props.parentPostType"
          :parentObjectId="props.parentObjectId"
          :parentPostActualId="props.parentPostActualId"
          :currentDepth="effectiveDepth + 1"
          @report-content="emit('report-content', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional styles for better text wrapping */
.break-words {
  word-break: break-word;
}

/* Smooth transitions for dropdown */
.dropdown-enter-active,
.dropdown-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Custom scrollbar for replies */
.max-h-64::-webkit-scrollbar {
  width: 4px;
}

.max-h-64::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.max-h-64::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 10px;
}

.max-h-64::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Mobile-specific styles */
@media (max-width: 640px) {
  .comment-item {
    padding-left: 0.25rem;
    padding-right: 0.25rem;
  }
}
</style>
