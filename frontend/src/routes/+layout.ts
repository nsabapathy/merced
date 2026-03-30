import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { refreshToken, getMe } from '$lib/api/auth';
import { authStore } from '$lib/stores/auth.svelte';
import { modelsStore } from '$lib/stores/models.svelte';
import { listModels } from '$lib/api/models';
import { listChats } from '$lib/api/chats';
import { chatStore } from '$lib/stores/chat.svelte';

export const ssr = false;
export const prerender = false;

export async function load({ url }: { url: URL }) {
  if (!browser) return {};

  const publicPaths = ['/login'];
  if (publicPaths.includes(url.pathname)) return {};

  if (authStore.accessToken) return {};

  try {
    const { access_token } = await refreshToken();
    authStore.setToken(access_token);
    const user = await getMe(access_token);
    authStore.setTokenAndUser(access_token, user);

    // Preload models and chats
    const [models, chats] = await Promise.all([listModels(), listChats()]);
    modelsStore.setModels(models);
    chatStore.setChats(chats);
  } catch {
    goto('/login');
  }

  return {};
}
