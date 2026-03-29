<script setup lang="ts">
const props = defineProps<{
  name: string
  location: string
  locationUrl?: string
  time: string
  description?: string
  category?: string
  isVisionExtracted?: boolean
}>()

const badgeLabel = computed(() => {
  if (props.description) return props.description
  if (props.category) return props.category.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  return 'Food Truck'
})

const searchTruck = (truckName: string) => {
  const cleanName = truckName.replace(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F900}-\u{1F9FF}]|[\u{1F018}-\u{1F270}]|[\u{238C}]|[\u{2764}]|[\u{FE0F}]/gu, '').trim();
  const searchQuery = encodeURIComponent(`${cleanName} food truck seattle`);
  window.open(`https://www.google.com/search?q=${searchQuery}`, '_blank');
}
</script>

<template>
  <div class="group p-8 rounded-2xl bg-white border border-outline-variant/20 shadow-sm hover:shadow-md transition-all duration-300">
    <div class="flex flex-col md:flex-row md:items-center justify-between">
      <div class="max-w-md">
        <h3
          @click="searchTruck(name)"
          class="font-headline text-3xl font-bold tracking-tight text-primary mb-2 cursor-pointer hover:text-primary-dim transition-colors"
        >
          {{ name }}
        </h3>
        <p class="font-body text-on-surface-variant text-sm flex items-center gap-2">
          <span class="material-symbols-outlined text-base text-primary-mint">location_on</span>
          <a
            v-if="locationUrl"
            :href="locationUrl"
            target="_blank"
            class="hover:text-primary transition-colors"
          >{{ location }}</a>
          <span v-else>{{ location }}</span>
        </p>
      </div>
      <div class="mt-6 md:mt-0 text-left md:text-right">
        <span class="font-label text-xs font-bold uppercase tracking-widest text-on-surface block mb-3">{{ time }}</span>
        <span class="bg-secondary-container text-primary-mint-dark text-[10px] px-4 py-1.5 rounded-full font-bold uppercase tracking-widest">
          {{ badgeLabel }}<span v-if="isVisionExtracted"> · AI</span>
        </span>
      </div>
    </div>
  </div>
</template>
