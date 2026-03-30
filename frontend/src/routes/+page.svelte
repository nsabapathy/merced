<script lang="ts">
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores/auth.svelte';
  import { onMount } from 'svelte';

  onMount(() => {
    if (authStore.isAuthenticated) {
      goto('/chat');
    } else {
      goto('/login');
    }
  });
</script>
