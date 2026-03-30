<script lang="ts">
  import { page } from '$app/state';
  import { authStore } from '$lib/stores/auth.svelte';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import Sidebar from '$lib/components/sidebar/Sidebar.svelte';
  import type { Snippet } from 'svelte';

  interface Props { children: Snippet; }
  let { children }: Props = $props();

  onMount(() => {
    if (!authStore.isAuthenticated) goto('/login');
    else if (!authStore.isAdmin) goto('/chat');
  });

  const tabs = [
    { label: 'Users', href: '/admin/users' },
    { label: 'Groups', href: '/admin/groups' }
  ];

  const currentPath = $derived(page.url.pathname);
</script>

<div class="flex h-screen bg-white overflow-hidden">
  <Sidebar />

  <div class="flex flex-col flex-1 min-w-0">
    <header class="flex items-center gap-1 px-6 pt-4 border-b border-gray-100">
      <span class="text-sm font-semibold text-gray-900 mr-4">Admin Panel</span>
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
