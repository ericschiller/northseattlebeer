<script setup lang="ts">
defineProps<{
  name: string
  location: string
  locationUrl?: string
  time: string
  description?: string
  isVisionExtracted?: boolean
}>()

const searchTruck = (truckName: string) => {
  const cleanName = truckName.replace(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F900}-\u{1F9FF}]|[\u{1F018}-\u{1F270}]|[\u{238C}]|[\u{2764}]|[\u{FE0F}]/gu, '').trim();
  const searchQuery = encodeURIComponent(`${cleanName} food truck seattle`);
  window.open(`https://www.google.com/search?q=${searchQuery}`, '_blank');
}
</script>

<template>
  <div class="flex flex-col md:flex-row md:items-end justify-between py-8 px-4 -mx-4 transition-colors duration-300">
    <div class="flex flex-col">
      <span class="font-label text-sm uppercase tracking-[0.2em] text-primary-mint font-bold mb-1">
        {{ description || 'Food Truck' }}
        <span v-if="isVisionExtracted" class="ml-1 text-xs text-tertiary">(AI Extracted)</span>
      </span>
      <h3 
        @click="searchTruck(name)"
        class="font-headline text-4xl font-medium tracking-tighter cursor-pointer hover:text-primary transition-colors"
      >
        {{ name }}
      </h3>
    </div>
    <div class="mt-4 md:mt-0 text-left">
      <div class="mb-1">
        <a 
          v-if="locationUrl"
          :href="locationUrl"
          target="_blank"
          class="font-label text-sm uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors border-b border-outline/20"
        >
          {{ location }}
        </a>
        <span v-else class="font-label text-sm uppercase tracking-widest text-on-surface-variant">
          {{ location }}
        </span>
      </div>
      <span class="block font-headline text-2xl font-bold text-primary">{{ time }}</span>
    </div>
  </div>
</template>
