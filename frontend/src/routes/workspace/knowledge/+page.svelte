<script lang="ts">
  import { onMount } from 'svelte';
  import { listCollections, createCollection, deleteCollection } from '$lib/api/knowledge';
  import { uiStore } from '$lib/stores/ui.svelte';
  import Spinner from '$lib/components/shared/Spinner.svelte';
  import EmptyState from '$lib/components/shared/EmptyState.svelte';
  import ConfirmDialog from '$lib/components/shared/ConfirmDialog.svelte';
  import type { CollectionRead } from '$lib/types/api';

  let loading = $state(true);
  let collections = $state<CollectionRead[]>([]);
  let confirmDeleteId = $state<string | null>(null);
  let newName = $state('');
  let creating = $state(false);

  onMount(async () => {
    try {
      collections = await listCollections();
    } catch {
      uiStore.addToast('Failed to load collections', 'error');
    } finally {
      loading = false;
    }
  });

  async function handleCreate(e: SubmitEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    creating = true;
    try {
      const c = await createCollection(newName.trim());
      collections = [c, ...collections];
      newName = '';
      uiStore.addToast('Collection created', 'success');
    } catch (err: unknown) {
      uiStore.addToast(err instanceof Error ? err.message : 'Failed to create', 'error');
    } finally {
      creating = false;
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteCollection(id);
      collections = collections.filter(c => c.id !== id);
      uiStore.addToast('Collection deleted', 'success');
    } catch {
      uiStore.addToast('Failed to delete collection', 'error');
    } finally {
      confirmDeleteId = null;
    }
  }
</script>

<svelte:head><title>Knowledge — Merced</title></svelte:head>

<div class="max-w-4xl">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-xl font-semibold text-gray-900">Knowledge <span class="text-gray-400 font-normal">{collections.length}</span></h1>
  </div>

  <!-- Create form -->
  <form onsubmit={handleCreate} class="flex gap-2 mb-6">
    <input
      bind:value={newName}
      placeholder="New collection name..."
      class="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm outline-none focus:border-gray-400"
    />
    <button type="submit" disabled={creating || !newName.trim()}
            class="px-4 py-2.5 rounded-xl bg-black text-white text-sm font-medium hover:bg-gray-800 disabled:opacity-60 transition-colors flex items-center gap-2">
      {#if creating}<Spinner size="sm" />{/if}
      Create
    </button>
  </form>

  {#if loading}
    <div class="flex justify-center py-12"><Spinner /></div>
  {:else if collections.length === 0}
    <EmptyState title="No knowledge collections" description="Create a collection and upload documents to enable RAG." />
  {:else}
    <div class="flex flex-col gap-2">
      {#each collections as col (col.id)}
        <a href="/workspace/knowledge/{col.id}"
           class="flex items-center gap-4 px-4 py-4 rounded-2xl border border-gray-100 hover:border-gray-200 transition-colors group">
          <div class="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center text-gray-500 shrink-0">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900">{col.name}</p>
            <p class="text-xs text-gray-400">{col.chroma_collection_name}</p>
          </div>
          <button
            onclick={(e) => { e.preventDefault(); confirmDeleteId = col.id; }}
            class="p-1.5 rounded-lg text-gray-300 group-hover:text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
            aria-label="Delete">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </a>
      {/each}
    </div>
  {/if}
</div>

<ConfirmDialog
  open={confirmDeleteId !== null}
  title="Delete collection?"
  description="All documents in this collection will also be removed."
  onconfirm={() => confirmDeleteId && handleDelete(confirmDeleteId)}
  oncancel={() => confirmDeleteId = null}
/>
