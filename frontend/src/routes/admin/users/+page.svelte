<script lang="ts">
  import { onMount } from 'svelte';
  import { listUsers, createUser, deleteUser } from '$lib/api/users';
  import { uiStore } from '$lib/stores/ui.svelte';
  import Spinner from '$lib/components/shared/Spinner.svelte';
  import Badge from '$lib/components/shared/Badge.svelte';
  import Avatar from '$lib/components/shared/Avatar.svelte';
  import EmptyState from '$lib/components/shared/EmptyState.svelte';
  import ConfirmDialog from '$lib/components/shared/ConfirmDialog.svelte';
  import type { UserRead, UserCreate } from '$lib/types/api';

  let loading = $state(true);
  let users = $state<UserRead[]>([]);
  let confirmDeleteId = $state<string | null>(null);
  let showForm = $state(false);
  let form = $state<UserCreate>({ email: '', username: '', password: '' });
  let saving = $state(false);

  onMount(async () => {
    try { users = await listUsers(); }
    catch { uiStore.addToast('Failed to load users', 'error'); }
    finally { loading = false; }
  });

  async function handleCreate(e: SubmitEvent) {
    e.preventDefault();
    saving = true;
    try {
      const u = await createUser(form);
      users = [...users, u];
      showForm = false;
      form = { email: '', username: '', password: '' };
      uiStore.addToast('User created', 'success');
    } catch (err: unknown) {
      uiStore.addToast(err instanceof Error ? err.message : 'Failed to create', 'error');
    } finally {
      saving = false;
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteUser(id);
      users = users.filter(u => u.id !== id);
      uiStore.addToast('User deleted', 'success');
    } catch {
      uiStore.addToast('Failed to delete user', 'error');
    } finally {
      confirmDeleteId = null;
    }
  }
</script>

<svelte:head><title>Users — Admin — Merced</title></svelte:head>

<div class="max-w-4xl">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-xl font-semibold text-gray-900">Users <span class="text-gray-400 font-normal">{users.length}</span></h1>
    <button onclick={() => showForm = !showForm}
            class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
      </svg>
      New User
    </button>
  </div>

  {#if showForm}
    <form onsubmit={handleCreate} class="mb-6 rounded-2xl border border-gray-200 p-5 flex flex-col gap-3">
      <h2 class="text-sm font-semibold text-gray-900">Create User</h2>
      <div class="grid grid-cols-2 gap-3">
        <input bind:value={form.email} type="email" placeholder="Email" required
               class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400" />
        <input bind:value={form.username} placeholder="Username" required
               class="px-3 py-2 rounded-lg border border-gray-200 text-sm outline-none focus:border-gray-400" />
        <input bind:value={form.password} type="password" placeholder="Password" required
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
          Create
        </button>
      </div>
    </form>
  {/if}

  {#if loading}
    <div class="flex justify-center py-12"><Spinner /></div>
  {:else if users.length === 0}
    <EmptyState title="No users" description="Create the first user account." />
  {:else}
    <div class="rounded-2xl border border-gray-100 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">User</th>
            <th class="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Email</th>
            <th class="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Role</th>
            <th class="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          {#each users as user (user.id)}
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3">
                <div class="flex items-center gap-2.5">
                  <Avatar username={user.username} size="sm" />
                  <span class="font-medium text-gray-900">{user.username}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-gray-500">{user.email}</td>
              <td class="px-4 py-3">
                <Badge variant={user.role === 'admin' ? 'info' : 'neutral'}>{user.role}</Badge>
              </td>
              <td class="px-4 py-3">
                <Badge variant={user.is_active ? 'success' : 'error'}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right">
                <button onclick={() => confirmDeleteId = user.id}
                        class="p-1.5 text-gray-300 hover:text-red-500 transition-colors" aria-label="Delete">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                  </svg>
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<ConfirmDialog
  open={confirmDeleteId !== null}
  title="Delete user?"
  description="This will permanently delete the user account and all their data."
  onconfirm={() => confirmDeleteId && handleDelete(confirmDeleteId)}
  oncancel={() => confirmDeleteId = null}
/>
