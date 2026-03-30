<script lang="ts">
  import { page } from '$app/state';
  import Sidebar from '$lib/components/sidebar/Sidebar.svelte';
  import { authStore } from '$lib/stores/auth.svelte';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import type { Snippet } from 'svelte';

  interface Props { children: Snippet; }
  let { children }: Props = $props();

  onMount(() => {
    if (!authStore.isAuthenticated) goto('/login');
  });

  const tabs = [
    { label: 'Models', href: '/workspace/models' },
    { label: 'Knowledge', href: '/workspace/knowledge' },
    { label: 'Prompts', href: '/workspace/prompts' }
  ];

  const currentPath = $derived(page.url.pathname);
</script>

<div class="flex h-screen bg-white overflow-hidden">
  <Sidebar />

  <div class="flex flex-col flex-1 min-w-0">
    <!-- Tab bar -->
    <header class="flex items-center gap-1 px-6 pt-4 border-b border-gray-100">
      {#each tabs as tab}
        <a
          href={tab.href}
          class="px-4 py-2.5 text-sm font-medium border-b-2 transition-colors
                 {currentPath.startsWith(tab.href)
                   ? 'border-gray-900 text-gray-900'
                   : 'border-transparent text-gray-400 hover:text-gray-700'}">
          {tab.label}
        </a>
      {/each}
    </header>

    <main class="flex-1 overflow-y-auto px-6 py-6">
      {@render children()}
    </main>
  </div>
</div>
