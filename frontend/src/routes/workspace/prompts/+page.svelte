<script lang="ts">
  import { onMount } from 'svelte';
  import { listPrompts, createPrompt, updatePrompt, deletePrompt } from '$lib/api/prompts';
  import { uiStore } from '$lib/stores/ui.svelte';
  import Spinner from '$lib/components/shared/Spinner.svelte';
  import EmptyState from '$lib/components/shared/EmptyState.svelte';
  import ConfirmDialog from '$lib/components/shared/ConfirmDialog.svelte';
  import type { PromptRead, PromptCreate } from '$lib/types/api';

  let loading = $state(true);
  let prompts = $state<PromptRead[]>([]);
  let confirmDeleteId = $state<string | null>(null);
  let showForm = $state(false);
  let editingId = $state<string | null>(null);
  let form = $state<PromptCreate>({ title: '', content: '', is_public: false });
  let saving = $state(false);

  onMount(async () => {
    try { prompts = await listPrompts(); }
    catch { uiStore.addToast('Failed to load prompts', 'error'); }
    finally { loading = false; }
  });

  function startEdit(p: PromptRead) {
    editingId = p.id;
    form = { title: p.title, content: p.content, is_public: p.is_public };
    showForm = true;
  }

  function resetForm() {
    showForm = false;
    editingId = null;
    form = { title: '', content: '', is_public: false };
  }

  async function handleSave(e: SubmitEvent) {
    e.preventDefault();
    saving = true;
    try {
      if (editingId) {
        const updated = await updatePrompt(editingId, form);
        prompts = prompts.map(p => p.id === editingId ? updated : p);
      } else {
        const created = await createPrompt(form);
        prompts = [created, ...prompts];
      }
      uiStore.addToast(editingId ? 'Prompt updated' : 'Prompt created', 'success');
      resetForm();
    } catch (err: unknown) {
      uiStore.addToast(err instanceof Error ? err.message : 'Failed to save', 'error');
    } finally {
      saving = false;
    }
  }

  async function handleDelete(id: string) {
    try {
      await deletePrompt(id);
      prompts = prompts.filter(p => p.id !== id);
      uiStore.addToast('Prompt deleted', 'success');
    } catch {
      uiStore.addToast('Failed to delete prompt', 'error');
    } finally {
      confirmDeleteId = null;
    }
  }
</script>

<svelte:head><title>Prompts — Merced</title></svelte:head>

<div class="max-w-4xl">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-xl font-semibold text-gray-900">Prompts <span class="text-gray-400 font-normal">{prompts.length}</span></h1>
    <button onclick={() => { resetForm(); showForm = true; }}
            class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
      </svg>
      New Prompt
    </button>
  </div>

  {#if showForm}
    <form onsubmit={handleSave} class="mb-6 rounded-2xl border border-gray-200 p-5 flex flex-col gap-3">
      <h2 class="text-sm font-semibold text-gray-900">{editingId ? 'Edit' : 'New'} Prompt</h2>
      <input bind:value={form.title} placeholder="Title" required
             class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400" />
      <textarea bind:value={form.content} placeholder="Prompt content..." required rows="4"
                class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400 resize-none"></textarea>
      <label class="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
        <input type="checkbox" bind:checked={form.is_public} class="rounded" />
        Make public (visible to all users)
      </label>
      <div class="flex gap-2 justify-end">
        <button type="button" onclick={resetForm}
                class="px-4 py-2 text-sm rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors">
          Cancel
        </button>
        <button type="submit" disabled={saving}
                class="px-4 py-2 text-sm rounded-lg bg-black text-white hover:bg-gray-800 disabled:opacity-60 transition-colors flex items-center gap-2">
          {#if saving}<Spinner size="sm" />{/if}
          Save
        </button>
      </div>
    </form>
  {/if}

  {#if loading}
    <div class="flex justify-center py-12"><Spinner /></div>
  {:else if prompts.length === 0}
    <EmptyState title="No prompts yet" description="Save reusable prompts to speed up your workflow." />
  {:else}
    <div class="flex flex-col gap-2">
      {#each prompts as prompt (prompt.id)}
        <div class="flex items-start gap-4 px-4 py-4 rounded-2xl border border-gray-100 hover:border-gray-200 transition-colors group">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <p class="text-sm font-medium text-gray-900">{prompt.title}</p>
              {#if prompt.is_public}
                <span class="text-xs px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-700">Public</span>
              {/if}
            </div>
            <p class="text-sm text-gray-500 line-clamp-2">{prompt.content}</p>
          </div>
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button onclick={() => startEdit(prompt)}
                    class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors" aria-label="Edit">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
              </svg>
            </button>
            <button onclick={() => confirmDeleteId = prompt.id}
                    class="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors" aria-label="Delete">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<ConfirmDialog
  open={confirmDeleteId !== null}
  title="Delete prompt?"
  description="This prompt will be permanently deleted."
  onconfirm={() => confirmDeleteId && handleDelete(confirmDeleteId)}
  oncancel={() => confirmDeleteId = null}
/>
