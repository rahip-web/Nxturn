<template>
  <div class="grid min-h-0 grid-cols-1 gap-4 lg:h-[calc(100vh-160px)] lg:grid-cols-[300px_minmax(0,1fr)] lg:gap-4">
    <ChatSidebar
      :selected-user-id="selectedUser?.id ?? null"
      :initial-username="$route.query.user?.toString() || ''"
      @selectUser="selectUser"
    />
    <ChatWindow :user="selectedUser" />
  </div>
</template>

<script>
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import ChatWindow from '../components/chat/ChatWindow.vue'

export default {
  components: { ChatSidebar, ChatWindow },
  data() {
    return {
      selectedUser: null,
    }
  },
  methods: {
    selectUser(user) {
      this.selectedUser = user
    },
  },
}
</script>
