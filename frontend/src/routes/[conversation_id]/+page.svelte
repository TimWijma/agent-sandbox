<script lang="ts">
	import Conversation from '$lib/components/Conversation.svelte';
	import { Conversation as ConversationDTO } from '$lib/DTO/Conversation.js';

	let { data } = $props();
	console.log(data);

	let conversation = $derived(() => {
		return new ConversationDTO(
			data.conversation.id,
			data.conversation.title,
			data.conversation.messages,
			data.conversation.createdAt,
			data.conversation.updatedAt
		);
	});

	// This effect will run whenever the data changes
	$effect(() => {
		const id = data.conversation.id;
		console.log(data.conversation);

		conversation = new ConversationDTO(
			id,
			data.conversation.title,
			data.conversation.messages,
			data.conversation.createdAt,
			data.conversation.updatedAt
		);
	});
</script>

<Conversation {conversation} />
