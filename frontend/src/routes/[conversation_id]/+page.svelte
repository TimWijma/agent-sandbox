<script lang="ts">
	import Conversation from '$lib/components/Conversation.svelte';
	import { Conversation as ConversationDTO } from '$lib/DTO/Conversation.js';

	let { data } = $props();
	let conversation = new ConversationDTO(
		data.conversation.id,
		data.conversation.title,
		data.conversation.messages,
		data.conversation.createdAt,
		data.conversation.updatedAt
	);
</script>

<Conversation {conversation} />
