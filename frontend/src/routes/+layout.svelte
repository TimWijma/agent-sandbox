<script lang="ts">
	import '../app.css';

	import { ConversationDTO as ConversationDTO } from '$lib/DTO/Conversation.js';
	import { Button } from '$lib/components/ui/button';
	import { chatManager, conversations } from '$lib/stores/globalStore';
	import { goto } from '$app/navigation';
	import { Plus } from '@lucide/svelte';
	import MenuItem from '$lib/components/MenuItem.svelte';

	let { data, children } = $props();
	$conversations = data.conversations;

	const createConversation = async () => {
		await chatManager
			.createConversation()
			.then((response) => {
				$conversations = [...$conversations, response];
				goto(`/${response.id}`, { invalidateAll: true });
				console.log('Conversation created:', response);
			})
			.catch((error) => {
				console.error('Error creating conversation:', error);
			});
	};
</script>

<div class="grid h-screen grid-cols-[250px_1fr] grid-rows-[auto_1fr] overflow-hidden">
	<aside class="row-span-2 overflow-y-auto border-r border-gray-200 bg-gray-100 p-4">
		<Button aria-label="Menu" class="w-full" on:click={createConversation}>
			<Plus class="mr-2" /> New Conversation
		</Button>
		<nav>
			<ul class="mt-4 space-y-2 text-gray-700">
				{#each $conversations as conversation}
					<MenuItem {conversation} />
				{/each}
			</ul>
		</nav>
	</aside>

	<header
		class="col-start-2 flex items-center justify-end space-x-4 border-b border-gray-200 bg-white p-4"
	></header>

	<main class="col-start-2 flex flex-col overflow-hidden bg-white">
		{@render children()}
	</main>
</div>
