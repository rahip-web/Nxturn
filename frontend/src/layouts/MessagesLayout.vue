<script setup lang="ts">
import TopNavBar from '@/components/layout/TopNavBar.vue'
import MobileBottomNav from '@/components/layout/MobileBottomNav.vue'
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="bg-gray-50 min-h-screen">
    <TopNavBar />
    <main class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 pb-safe-mobile lg:pb-4">
      <div class="min-w-0">
        <RouterView />
      </div>
    </main>
    <MobileBottomNav />
  </div>
</template>

<style scoped>
.pb-safe-mobile {
  padding-bottom: 0;
}
@media (max-width: 1023px) {
  .pb-safe-mobile {
    padding-bottom: calc(3rem + env(safe-area-inset-bottom, 0));
  }
}
</style>
