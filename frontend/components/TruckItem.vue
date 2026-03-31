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
</script>

<template>
  <div class="group p-8 rounded-lg bg-[#FFFFFF] border border-[#1E293B]/10 shadow-[0px_4px_6px_-1px_rgba(0,0,0,0.1)] transition-all duration-300 hover:border-primary-mint/30 hover:shadow-md">
    <div class="flex flex-col md:flex-row md:items-center justify-between">
      <div class="max-w-md">
        <h3
          class="font-headline text-[1.25rem] font-bold tracking-tight text-[#1E293B] mb-2 transition-colors group-hover:text-primary-mint-dark"
        >
          {{ name }}
        </h3>
        <p class="font-body text-[#64748B] text-[0.875rem] flex items-center gap-2">
          <span class="material-symbols-outlined text-base text-[#1E293B]">location_on</span>
          <a
            v-if="locationUrl"
            :href="locationUrl"
            target="_blank"
            class="hover:text-[#F97316] transition-colors"
          >{{ location }}</a>
          <span v-else>{{ location }}</span>
        </p>
      </div>
      <div class="mt-6 md:mt-0 text-left md:text-right">
        <span class="font-label text-[0.875rem] font-bold uppercase tracking-widest text-[#64748B] block mb-3">{{ time }}</span>
        <span class="bg-[#D1FAE5] text-[#065F46] text-[0.75rem] px-4 py-1.5 rounded-full font-bold uppercase tracking-widest">
          {{ badgeLabel }}<span v-if="isVisionExtracted"> · AI</span>
        </span>
      </div>
    </div>
  </div>
</template>
