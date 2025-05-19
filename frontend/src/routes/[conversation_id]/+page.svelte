<script lang="ts">
	import Conversation from '$lib/components/Conversation.svelte';
	import { ConversationDTO } from '$lib/DTO/Conversation.js';

	let { data } = $props();

	let conversation: ConversationDTO = $derived(data.conversation);
</script>

{#key conversation.id}
	<Conversation {conversation} />
{/key}
