<script lang="ts">
  import { page } from '$app/state';
  import { onMount } from 'svelte';
  import { getGroupMembers, addMember, removeMember } from '$lib/api/groups';
  import { listUsers } from '$lib/api/users';
  import { uiStore } from '$lib/stores/ui.svelte';
  import Spinner from '$lib/components/shared/Spinner.svelte';
  import Avatar from '$lib/components/shared/Avatar.svelte';
  import EmptyState from '$lib/components/shared/EmptyState.svelte';
  import ConfirmDialog from '$lib/components/shared/ConfirmDialog.svelte';
  import type { UserRead } from '$lib/types/api';

  const groupId = $derived(page.params.id ?? '');
  const groupName = $derived(page.url.searchParams.get('name') ?? 'Group');

  let loading = $state(true);
  let members = $state<{ id: string; username: string; email: string }[]>([]);
  let allUsers = $state<UserRead[]>([]);
  let confirmRemoveId = $state<string | null>(null);
  let showAddForm = $state(false);
  let selectedUserId = $state('');
  let saving = $state(false);

  const nonMembers = $derived(
    allUsers.filter(u => !members.some(m => m.id === u.id))
  );

  onMount(async () => {
    try {
      [members, allUsers] = await Promise.all([
        getGroupMembers(groupId),
        listUsers()
      ]);
    } catch {
      uiStore.addToast('Failed to load group members', 'error');
    } finally {
      loading = false;
    }
  });

  async function handleAddMember() {
    if (!selectedUserId) return;
    saving = true;
    try {
      await addMember(groupId, selectedUserId);
      const user = allUsers.find(u => u.id === selectedUserId);
      if (user) members = [...members, { id: user.id, username: user.username, email: user.email }];
      selectedUserId = '';
      showAddForm = false;
      uiStore.addToast('Member added', 'success');
    } catch (err: unknown) {
      uiStore.addToast(err instanceof Error ? err.message : 'Failed to add member', 'error');
    } finally {
      saving = false;
    }
  }

  async function handleRemoveMember(userId: string) {
    try {
      await removeMember(groupId, userId);
      members = members.filter(m => m.id !== userId);
      uiStore.addToast('Member removed', 'success');
    } catch {
      uiStore.addToast('Failed to remove member', 'error');
    } finally {
      confirmRemoveId = null;
    }
  }
</script>

<svelte:head><title>{groupName} — Groups — Admin — Merced</title></svelte:head>

<div class="max-w-3xl">
  <div class="mb-6">
    <a href="/admin/groups" class="text-xs text-gray-400 hover:text-gray-600 transition-colors">← Groups</a>
    <h1 class="text-xl font-semibold text-gray-900 mt-1">{groupName}</h1>
    <p class="text-sm text-gray-400">Manage group members</p>
  </div>

  <div class="flex items-center justify-between mb-4">
    <p class="text-sm font-medium text-gray-700">
      Members <span class="text-gray-400 font-normal">{members.length}</span>
    </p>
    <button onclick={() => showAddForm = !showAddForm}
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
      </svg>
      Add Member
    </button>
  </div>

  {#if showAddForm}
    <div class="mb-4 rounded-xl border border-gray-200 p-4 flex flex-col gap-3">
      <h2 class="text-sm font-semibold text-gray-900">Add Member</h2>
      {#if nonMembers.length === 0}
        <p class="text-sm text-gray-400">All users are already members.</p>
      {:else}
        <select bind:value={selectedUserId}
                class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400 bg-white">
          <option value="">Select a user...</option>
          {#each nonMembers as user}
            <option value={user.id}>{user.username} ({user.email})</option>
          {/each}
        </select>
        <div class="flex gap-2 justify-end">
          <button onclick={() => showAddForm = false}
                  class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors">
            Cancel
          </button>
          <button onclick={handleAddMember} disabled={!selectedUserId || saving}
                  class="px-3 py-1.5 text-sm rounded-lg bg-black text-white hover:bg-gray-800 disabled:opacity-60 transition-colors flex items-center gap-2">
            {#if saving}<Spinner size="sm" />{/if}
            Add
          </button>
        </div>
      {/if}
    </div>
  {/if}

  {#if loading}
    <div class="flex justify-center py-8"><Spinner /></div>
  {:else if members.length === 0}
    <EmptyState title="No members" description="Add users to grant them group permissions." />
  {:else}
    <div class="flex flex-col gap-2">
      {#each members as member (member.id)}
        <div class="flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-100 group">
          <Avatar username={member.username} size="sm" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900">{member.username}</p>
            <p class="text-xs text-gray-400">{member.email}</p>
          </div>
          <button
            onclick={() => confirmRemoveId = member.id}
            class="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
            aria-label="Remove">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M13 7a4 4 0 11-8 0 4 4 0 018 0zM9 14a6 6 0 00-6 6v1h12v-1a6 6 0 00-6-6zM21 12h-6"/>
            </svg>
          </button>
        </div>
      {/each}
    </div>
  {/if}
</div>

<ConfirmDialog
  open={confirmRemoveId !== null}
  title="Remove member?"
  description="This user will lose permissions associated with this group."
  onconfirm={() => confirmRemoveId && handleRemoveMember(confirmRemoveId)}
  oncancel={() => confirmRemoveId = null}
/>
