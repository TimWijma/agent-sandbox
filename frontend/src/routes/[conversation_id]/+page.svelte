<script lang="ts">
	import Conversation from '$lib/components/Conversation.svelte';

	let { data } = $props();
	let conversation = data.conversation;
</script>

<Conversation {conversation} />
