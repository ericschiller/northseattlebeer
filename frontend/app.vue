<template>
  <div class="bg-surface text-on-surface min-h-screen font-body selection:bg-primary-mint/30">
    <NuxtPage />
    <AppFooter />
  </div>
</template>

<style>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  vertical-align: middle;
}

/* Custom scrollbar for a more integrated feel */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #f9fffb;
}
::-webkit-scrollbar-thumb {
  background: #d4e0db;
}
::-webkit-scrollbar-thumb:hover {
  background: #aab4b0;
}
</style>
