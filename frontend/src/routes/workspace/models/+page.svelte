<script lang="ts">
  import { onMount } from 'svelte';
  import { listModels, deleteModel, updateModel, createModel } from '$lib/api/models';
  import { uiStore } from '$lib/stores/ui.svelte';
  import { modelsStore } from '$lib/stores/models.svelte';
  import Spinner from '$lib/components/shared/Spinner.svelte';
  import EmptyState from '$lib/components/shared/EmptyState.svelte';
  import ConfirmDialog from '$lib/components/shared/ConfirmDialog.svelte';
  import type { ModelConfigRead, ModelConfigCreate } from '$lib/types/api';

  let loading = $state(true);
  let models = $state<ModelConfigRead[]>([]);
  let confirmDeleteId = $state<string | null>(null);
  let showForm = $state(false);
  let form = $state<ModelConfigCreate>({ name: '', base_url: '', api_key: '', model_id: '', is_active: true });
  let saving = $state(false);

  onMount(async () => {
    try {
      models = await listModels();
    } catch {
      uiStore.addToast('Failed to load models', 'error');
    } finally {
      loading = false;
    }
  });

  async function handleDelete(id: string) {
    try {
      await deleteModel(id);
      models = models.filter(m => m.id !== id);
      modelsStore.setModels(models);
      uiStore.addToast('Model deleted', 'success');
    } catch {
      uiStore.addToast('Failed to delete model', 'error');
    } finally {
      confirmDeleteId = null;
    }
  }

  async function handleToggle(model: ModelConfigRead) {
    try {
      const updated = await updateModel(model.id, { is_active: !model.is_active });
      models = models.map(m => m.id === updated.id ? updated : m);
    } catch {
      uiStore.addToast('Failed to update model', 'error');
    }
  }

  async function handleCreate(e: SubmitEvent) {
    e.preventDefault();
    saving = true;
    try {
      const m = await createModel(form);
      models = [m, ...models];
      modelsStore.setModels(models);
      showForm = false;
      form = { name: '', base_url: '', api_key: '', model_id: '', is_active: true };
      uiStore.addToast('Model created', 'success');
    } catch (err: unknown) {
      uiStore.addToast(err instanceof Error ? err.message : 'Failed to create model', 'error');
    } finally {
      saving = false;
    }
  }
</script>

<svelte:head><title>Models — Merced</title></svelte:head>

<div class="max-w-4xl">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-xl font-semibold text-gray-900">Models <span class="text-gray-400 font-normal">{models.length}</span></h1>
    <button
      onclick={() => showForm = true}
      class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
      </svg>
      New Model
    </button>
  </div>

  <!-- New model form -->
  {#if showForm}
    <form onsubmit={handleCreate}
          class="mb-6 rounded-2xl border border-gray-200 p-5 flex flex-col gap-3">
      <h2 class="text-sm font-semibold text-gray-900">Add Model</h2>
      <div class="grid grid-cols-2 gap-3">
        <input bind:value={form.name} placeholder="Display name" required
               class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400" />
        <input bind:value={form.model_id} placeholder="Model ID (e.g. gpt-4o)" required
               class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400" />
        <input bind:value={form.base_url} placeholder="Base URL" required
               class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400 col-span-2" />
        <input bind:value={form.api_key} type="password" placeholder="API Key" required
               class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400 col-span-2" />
      </div>
      <div class="flex gap-2 justify-end">
        <button type="button" onclick={() => showForm = false}
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

  <!-- Model list -->
  {#if loading}
    <div class="flex justify-center py-12"><Spinner /></div>
  {:else if models.length === 0}
    <EmptyState title="No models yet" description="Add your first OpenAI-compatible model to get started." />
  {:else}
    <div class="flex flex-col gap-2">
      {#each models as model (model.id)}
        <div class="flex items-center gap-4 px-4 py-4 rounded-2xl border border-gray-100 hover:border-gray-200 transition-colors">
          <div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center text-white text-xs font-bold shrink-0">
            OI
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900">{model.name}</p>
            <p class="text-xs text-gray-400 truncate">{model.model_id} · {model.base_url}</p>
          </div>
          <div class="flex items-center gap-3">
            <!-- Toggle -->
            <button
              onclick={() => handleToggle(model)}
              class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors
                     {model.is_active ? 'bg-green-500' : 'bg-gray-200'}"
              aria-label="Toggle active">
              <span class="inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform
                           {model.is_active ? 'translate-x-4' : 'translate-x-0.5'}"></span>
            </button>
            <!-- Delete -->
            <button
              onclick={() => confirmDeleteId = model.id}
              class="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              aria-label="Delete">
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
  title="Delete model?"
  description="This will permanently remove the model configuration."
  onconfirm={() => confirmDeleteId && handleDelete(confirmDeleteId)}
  oncancel={() => confirmDeleteId = null}
/>
