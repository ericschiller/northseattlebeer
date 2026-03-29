<script setup lang="ts">
const props = defineProps<{
  haiku?: string
}>()

const haikuLines = computed(() => {
  if (!props.haiku) return []
  return props.haiku.split('\n').filter(line => line.trim())
})
</script>

<template>
  <div v-if="haiku" class="mb-12 py-8 border-y-2 border-outline-variant/10 text-center">
    <p v-for="(line, index) in haikuLines" :key="index" class="font-body text-lg italic text-on-surface-variant/80">
      {{ line }}
    </p>
  </div>
</template>
