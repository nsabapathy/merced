<script lang="ts">
  import { goto } from '$app/navigation';
  import { login, getMe } from '$lib/api/auth';
  import { authStore } from '$lib/stores/auth.svelte';
  import { modelsStore } from '$lib/stores/models.svelte';
  import { chatStore } from '$lib/stores/chat.svelte';
  import { listModels } from '$lib/api/models';
  import { listChats } from '$lib/api/chats';
  import { uiStore } from '$lib/stores/ui.svelte';
  import Spinner from '$lib/components/shared/Spinner.svelte';

  let email = $state('');
  let password = $state('');
  let showPassword = $state(false);
  let loading = $state(false);
  let error = $state('');

  async function handleLogin(e: SubmitEvent) {
    e.preventDefault();
    if (loading) return;
    error = '';
    loading = true;

    try {
      const { access_token } = await login(email, password);
      authStore.setToken(access_token);
      const user = await getMe(access_token);
      authStore.setTokenAndUser(access_token, user);

      const [models, chats] = await Promise.all([listModels(), listChats()]);
      modelsStore.setModels(models);
      chatStore.setChats(chats);

      goto('/chat');
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Invalid credentials';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head><title>Sign in — Merced</title></svelte:head>

<div class="min-h-screen bg-white flex flex-col">
  <!-- Logo top-left -->
  <header class="p-6">
    <div class="flex items-center justify-center w-8 h-8 rounded-md bg-black text-white text-sm font-bold">
      OI
    </div>
  </header>

  <!-- Centered form -->
  <main class="flex-1 flex items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <h1 class="text-2xl font-bold text-gray-900 text-center mb-8">
        Sign in to Merced
      </h1>

      <form onsubmit={handleLogin} class="flex flex-col gap-4">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-900 mb-1.5">Email</label>
          <input
            id="email"
            type="email"
            bind:value={email}
            placeholder="Enter Your Email"
            required
            class="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm text-gray-900
                   placeholder-gray-400 outline-none focus:border-gray-400 transition-colors bg-white"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-900 mb-1.5">Password</label>
          <div class="relative">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              bind:value={password}
              placeholder="Enter Your Password"
              required
              class="w-full px-4 py-3 pr-11 rounded-xl border border-gray-200 text-sm text-gray-900
                     placeholder-gray-400 outline-none focus:border-gray-400 transition-colors bg-white"
            />
            <button
              type="button"
              onclick={() => showPassword = !showPassword}
              class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors">
              {#if showPassword}
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                </svg>
              {:else}
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
              {/if}
            </button>
          </div>
        </div>

        {#if error}
          <p class="text-sm text-red-600 text-center">{error}</p>
        {/if}

        <button
          type="submit"
          disabled={loading}
          class="w-full py-3 rounded-full bg-gray-100 text-sm font-medium text-gray-900
                 hover:bg-gray-200 disabled:opacity-60 disabled:cursor-not-allowed
                 transition-colors flex items-center justify-center gap-2 mt-2">
          {#if loading}
            <Spinner size="sm" />
          {/if}
          Sign in
        </button>
      </form>
    </div>
  </main>
</div>
