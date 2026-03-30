<script lang="ts">
  import { authStore } from '$lib/stores/auth.svelte';
  import { goto } from '$app/navigation';
  import Sidebar from '$lib/components/sidebar/Sidebar.svelte';
  import ModelSelector from '$lib/components/chat/ModelSelector.svelte';
  import Avatar from '$lib/components/shared/Avatar.svelte';
  import type { Snippet } from 'svelte';
  import { onMount } from 'svelte';

  interface Props { children: Snippet; }
  let { children }: Props = $props();

  onMount(() => {
    if (!authStore.isAuthenticated) goto('/login');
  });
</script>

<div class="flex h-screen bg-white overflow-hidden">
  <Sidebar />

  <div class="flex flex-col flex-1 min-w-0">
    <!-- Top bar -->
    <header class="flex items-center justify-between px-6 py-3 border-b border-gray-100 shrink-0">
      <div class="flex flex-col">
        <ModelSelector />
        <span class="text-xs text-gray-400 mt-0.5">Set as default</span>
      </div>
      <div class="flex items-center gap-3">
        <button class="p-2 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
                aria-label="Settings">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
        </button>
        <Avatar username={authStore.currentUser?.username ?? 'U'} size="sm" />
      </div>
    </header>

    <!-- Page content -->
    <main class="flex-1 min-h-0">
      {@render children()}
    </main>
  </div>
</div>
