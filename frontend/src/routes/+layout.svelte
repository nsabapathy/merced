<script lang="ts">
  import '../app.css';
  import ToastContainer from '$lib/components/shared/ToastContainer.svelte';
  import type { Snippet } from 'svelte';

  interface Props { children: Snippet; }
  let { children }: Props = $props();
</script>

{@render children()}
<ToastContainer />
