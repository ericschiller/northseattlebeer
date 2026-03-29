<script setup lang="ts">
defineProps<{
  dayName: string
  monthDay: string
}>()
</script>

<template>
  <section>
    <div class="mb-10 pb-4 border-b border-outline/5">
      <h2 class="font-headline text-3xl font-bold uppercase tracking-tight">
        {{ dayName }}, <span class="text-primary">{{ monthDay }}</span>
      </h2>
    </div>
    <div class="space-y-0 divide-y divide-outline/5">
      <slot />
    </div>
  </section>
</template>
