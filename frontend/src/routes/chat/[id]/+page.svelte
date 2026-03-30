<script lang="ts">
  import { page } from '$app/state';
  import { getChat } from '$lib/api/chats';
  import { chatStore } from '$lib/stores/chat.svelte';
  import { uiStore } from '$lib/stores/ui.svelte';
  import { getSocket } from '$lib/socket';
  import ChatWindow from '$lib/components/chat/ChatWindow.svelte';
  import Spinner from '$lib/components/shared/Spinner.svelte';
  import type { MessageRead } from '$lib/types/api';

  const chatId = $derived(page.params.id ?? '');
  let loading = $state(false);

  $effect(() => {
    const id = chatId;
    loading = true;
    chatStore.clear();

    getChat(id)
      .then(detail => chatStore.setActiveChat(detail, detail.messages))
      .catch(() => uiStore.addToast('Failed to load chat', 'error'))
      .finally(() => loading = false);

    const socket = getSocket();
    socket.emit('join_chat', { chat_id: id });

    const onChunk = (data: { chunk: string }) => chatStore.appendChunk(data.chunk);
    const onEnd = (data: { content: string; message_id: string }) => {
      const msg: MessageRead = {
        id: data.message_id,
        chat_id: id,
        role: 'assistant',
        content: data.content,
        token_count: 0,
        model_id: null,
        knowledge_used: false,
        created_at: new Date().toISOString()
      };
      chatStore.finalizeStream(msg);
    };
    const onError = (data: { error: string }) => {
      chatStore.isStreaming = false;
      uiStore.addToast(data.error, 'error');
    };

    socket.on('stream_chunk', onChunk);
    socket.on('stream_end', onEnd);
    socket.on('stream_error', onError);

    return () => {
      socket.emit('leave_chat', { chat_id: id });
      socket.off('stream_chunk', onChunk);
      socket.off('stream_end', onEnd);
      socket.off('stream_error', onError);
    };
  });
</script>

<svelte:head>
  <title>{chatStore.activeChat?.title ?? 'Chat'} — Merced</title>
</svelte:head>

{#if loading}
  <div class="flex h-full items-center justify-center">
    <Spinner />
  </div>
{:else}
  <ChatWindow {chatId} />
{/if}
