<script lang="ts">
  import { goto } from '$app/navigation';
  import { createChat } from '$lib/api/chats';
  import { chatStore } from '$lib/stores/chat.svelte';
  import { modelsStore } from '$lib/stores/models.svelte';
  import ModelSelector from '$lib/components/chat/ModelSelector.svelte';
  import SuggestedPrompts from '$lib/components/chat/SuggestedPrompts.svelte';
  import ChatInput from '$lib/components/chat/ChatInput.svelte';
  import { uiStore } from '$lib/stores/ui.svelte';

  let pendingText = $state('');
  let tempChatId = $state<string | null>(null);

  async function ensureChat(): Promise<string> {
    if (tempChatId) return tempChatId;
    const chat = await createChat();
    chatStore.addChat(chat);
    tempChatId = chat.id;
    goto(`/chat/${chat.id}`, { replaceState: true });
    return chat.id;
  }

  async function handleSuggestion(text: string) {
    pendingText = text;
  }
</script>

<svelte:head><title>New Chat — Merced</title></svelte:head>

<div class="flex flex-col h-full items-center justify-center px-6 pb-6">
  <!-- Model branding -->
  <div class="flex items-center gap-4 mb-12">
    <div class="w-12 h-12 rounded-xl bg-black flex items-center justify-center text-white font-bold text-lg">
      OI
    </div>
    <h2 class="text-3xl font-semibold text-gray-900 tracking-tight">
      {modelsStore.selectedModel?.name ?? 'Merced AI'}
    </h2>
  </div>

  <!-- Input card -->
  <div class="w-full max-w-2xl">
    {#if tempChatId}
      <ChatInput chatId={tempChatId} prefill={pendingText} />
    {:else}
      <!-- Fake input that creates chat on first send -->
      <div class="w-full">
        <div class="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
          <textarea
            bind:value={pendingText}
            placeholder="How can I help you today?"
            rows="1"
            onkeydown={async (e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!pendingText.trim()) return;
                const id = await ensureChat();
              }
            }}
            class="w-full px-4 pt-4 pb-2 text-sm text-gray-900 placeholder-gray-400 resize-none outline-none bg-transparent"
            style="min-height: 52px;"
          ></textarea>
          <div class="flex items-center justify-between px-3 pb-3">
            <div class="flex items-center gap-1">
              <button class="p-2 rounded-xl text-gray-400 hover:bg-gray-100 transition-colors" aria-label="Attach">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4v16m8-8H4"/>
                </svg>
              </button>
              <button class="p-2 rounded-xl text-gray-400 hover:bg-gray-100 transition-colors" aria-label="Prompts">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                        d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
                </svg>
              </button>
            </div>
            <div class="flex items-center gap-2">
              <button class="p-2 rounded-xl text-gray-400 hover:bg-gray-100 transition-colors" aria-label="Mic">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                        d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
                </svg>
              </button>
              <button
                onclick={async () => { if (pendingText.trim()) await ensureChat(); }}
                disabled={!pendingText.trim()}
                class="p-2 rounded-full bg-black text-white hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Suggested prompts -->
  <div class="mt-6 w-full max-w-2xl">
    <SuggestedPrompts onselect={(t) => pendingText = t} />
  </div>
</div>
