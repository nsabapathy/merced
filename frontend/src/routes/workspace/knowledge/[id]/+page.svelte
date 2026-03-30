<script lang="ts">
  import { page } from '$app/state';
  import { onMount, onDestroy } from 'svelte';
  import { getCollection, listDocuments, addDocument, deleteDocument } from '$lib/api/knowledge';
  import { uploadFile } from '$lib/api/files';
  import { uiStore } from '$lib/stores/ui.svelte';
  import Spinner from '$lib/components/shared/Spinner.svelte';
  import Badge from '$lib/components/shared/Badge.svelte';
  import ConfirmDialog from '$lib/components/shared/ConfirmDialog.svelte';
  import type { CollectionRead, DocumentRead } from '$lib/types/api';

  const collectionId = $derived(page.params.id ?? '');

  let collection = $state<CollectionRead | null>(null);
  let documents = $state<DocumentRead[]>([]);
  let loading = $state(true);
  let uploading = $state(false);
  let fileInput = $state<HTMLInputElement>();
  let confirmDeleteId = $state<string | null>(null);
  let pollInterval: ReturnType<typeof setInterval> | null = null;

  onMount(async () => {
    try {
      [collection, documents] = await Promise.all([
        getCollection(collectionId),
        listDocuments(collectionId)
      ]);
      startPollingIfNeeded();
    } catch {
      uiStore.addToast('Collection not found', 'error');
    } finally {
      loading = false;
    }
  });

  onDestroy(() => { if (pollInterval) clearInterval(pollInterval); });

  function startPollingIfNeeded() {
    const hasActive = documents.some(d => d.status === 'pending' || d.status === 'processing');
    if (hasActive && !pollInterval) {
      pollInterval = setInterval(async () => {
        try {
          documents = await listDocuments(collectionId);
          const stillActive = documents.some(d => d.status === 'pending' || d.status === 'processing');
          if (!stillActive && pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
          }
        } catch { /* ignore */ }
      }, 3000);
    }
  }

  async function handleFileUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    uploading = true;
    try {
      const uploaded = await uploadFile(file);
      const doc = await addDocument(collectionId, uploaded.id, file.name);
      documents = [...documents, doc];
      uiStore.addToast('Document uploaded — indexing in background', 'success');
      startPollingIfNeeded();
    } catch (err: unknown) {
      uiStore.addToast(err instanceof Error ? err.message : 'Upload failed', 'error');
    } finally {
      uploading = false;
      input.value = '';
    }
  }

  async function handleDeleteDoc(docId: string) {
    try {
      await deleteDocument(collectionId, docId);
      documents = documents.filter(d => d.id !== docId);
    } catch {
      uiStore.addToast('Failed to delete document', 'error');
    } finally {
      confirmDeleteId = null;
    }
  }

  const statusVariant = (status: DocumentRead['status']) => {
    const map: Record<string, 'success' | 'error' | 'warning' | 'info'> = {
      indexed: 'success', failed: 'error', processing: 'info', pending: 'warning'
    };
    return map[status] ?? 'neutral';
  };
</script>

<svelte:head><title>{collection?.name ?? 'Collection'} — Knowledge — Merced</title></svelte:head>

{#if loading}
  <div class="flex justify-center py-12"><Spinner /></div>
{:else if collection}
  <div class="max-w-3xl">
    <div class="mb-6">
      <a href="/workspace/knowledge" class="text-xs text-gray-400 hover:text-gray-600 transition-colors">← Knowledge</a>
      <h1 class="text-xl font-semibold text-gray-900 mt-1">{collection.name}</h1>
      <p class="text-sm text-gray-400">{collection.chroma_collection_name}</p>
    </div>

    <!-- Upload -->
    <div class="mb-6">
      <input bind:this={fileInput} type="file" class="hidden" onchange={handleFileUpload}
             accept=".pdf,.docx,.doc,.txt" />
      <button
        onclick={() => fileInput?.click()}
        disabled={uploading}
        class="flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 border-dashed border-gray-200
               text-sm text-gray-500 hover:border-gray-400 hover:text-gray-700 disabled:opacity-60 transition-colors">
        {#if uploading}
          <Spinner size="sm" />
          Uploading...
        {:else}
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
          </svg>
          Upload document (PDF, DOCX, TXT)
        {/if}
      </button>
    </div>

    <!-- Document list -->
    {#if documents.length === 0}
      <p class="text-sm text-gray-400">No documents yet. Upload one to get started.</p>
    {:else}
      <div class="flex flex-col gap-2">
        {#each documents as doc (doc.id)}
          <div class="flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-100 group">
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 truncate">{doc.title}</p>
              <p class="text-xs text-gray-400">
                {doc.chunk_count} chunks
                {#if doc.status === 'failed' && doc.error_message}
                  · <span class="text-red-500">{doc.error_message}</span>
                {/if}
              </p>
            </div>
            <div class="flex items-center gap-2">
              {#if doc.status === 'pending' || doc.status === 'processing'}
                <Spinner size="sm" />
              {/if}
              <Badge variant={statusVariant(doc.status)}>{doc.status}</Badge>
            </div>
            <button onclick={() => confirmDeleteId = doc.id}
                    class="p-1.5 text-gray-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                    aria-label="Delete">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>
{/if}

<ConfirmDialog
  open={confirmDeleteId !== null}
  title="Delete document?"
  description="This will remove the document and its indexed chunks from the collection."
  onconfirm={() => confirmDeleteId && handleDeleteDoc(confirmDeleteId)}
  oncancel={() => confirmDeleteId = null}
/>
