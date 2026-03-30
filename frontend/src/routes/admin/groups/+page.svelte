<script lang="ts">
  import { onMount } from 'svelte';
  import { listGroups, createGroup, deleteGroup } from '$lib/api/groups';
  import { uiStore } from '$lib/stores/ui.svelte';
  import Spinner from '$lib/components/shared/Spinner.svelte';
  import EmptyState from '$lib/components/shared/EmptyState.svelte';
  import ConfirmDialog from '$lib/components/shared/ConfirmDialog.svelte';
  import type { GroupRead, GroupCreate } from '$lib/types/api';

  let loading = $state(true);
  let groups = $state<GroupRead[]>([]);
  let confirmDeleteId = $state<string | null>(null);
  let showForm = $state(false);
  let form = $state<GroupCreate>({ name: '', description: '' });
  let saving = $state(false);

  onMount(async () => {
    try { groups = await listGroups(); }
    catch { uiStore.addToast('Failed to load groups', 'error'); }
    finally { loading = false; }
  });

  async function handleCreate(e: SubmitEvent) {
    e.preventDefault();
    saving = true;
    try {
      const g = await createGroup(form);
      groups = [...groups, g];
      showForm = false;
      form = { name: '', description: '' };
      uiStore.addToast('Group created', 'success');
    } catch (err: unknown) {
      uiStore.addToast(err instanceof Error ? err.message : 'Failed to create', 'error');
    } finally {
      saving = false;
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteGroup(id);
      groups = groups.filter(g => g.id !== id);
      uiStore.addToast('Group deleted', 'success');
    } catch {
      uiStore.addToast('Failed to delete group', 'error');
    } finally {
      confirmDeleteId = null;
    }
  }
</script>

<svelte:head><title>Groups — Admin — Merced</title></svelte:head>

<div class="max-w-4xl">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-xl font-semibold text-gray-900">Groups <span class="text-gray-400 font-normal">{groups.length}</span></h1>
    <button onclick={() => showForm = !showForm}
            class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
      </svg>
      New Group
    </button>
  </div>

  {#if showForm}
    <form onsubmit={handleCreate} class="mb-6 rounded-2xl border border-gray-200 p-5 flex flex-col gap-3">
      <h2 class="text-sm font-semibold text-gray-900">Create Group</h2>
      <input bind:value={form.name} placeholder="Group name" required
             class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400" />
      <input bind:value={form.description} placeholder="Description (optional)"
             class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400" />
      <div class="flex gap-2 justify-end">
        <button type="button" onclick={() => showForm = false}
                class="px-4 py-2 text-sm rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors">
          Cancel
        </button>
        <button type="submit" disabled={saving}
                class="px-4 py-2 text-sm rounded-lg bg-black text-white hover:bg-gray-800 disabled:opacity-60 transition-colors flex items-center gap-2">
          {#if saving}<Spinner size="sm" />{/if}
          Create
        </button>
      </div>
    </form>
  {/if}

  {#if loading}
    <div class="flex justify-center py-12"><Spinner /></div>
  {:else if groups.length === 0}
    <EmptyState title="No groups" description="Create groups to manage user permissions." />
  {:else}
    <div class="flex flex-col gap-2">
      {#each groups as group (group.id)}
        <div class="flex items-center gap-4 px-4 py-4 rounded-2xl border border-gray-100 hover:border-gray-200 transition-colors group">
          <div class="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center shrink-0">
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <a href="/admin/groups/{group.id}?name={encodeURIComponent(group.name)}"
               class="text-sm font-medium text-gray-900 hover:text-black hover:underline">{group.name}</a>
            {#if group.description}
              <p class="text-xs text-gray-400 truncate">{group.description}</p>
            {/if}
          </div>
          <button
            onclick={() => confirmDeleteId = group.id}
            class="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
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

<ConfirmDialog
  open={confirmDeleteId !== null}
  title="Delete group?"
  description="Members will lose permissions associated with this group."
  onconfirm={() => confirmDeleteId && handleDelete(confirmDeleteId)}
  oncancel={() => confirmDeleteId = null}
/>
