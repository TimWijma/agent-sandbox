<script lang="ts">
	import '../app.css';
	import { Conversation as ConversationDTO } from '$lib/DTO/Conversation.js';
	import { Button } from '$lib/components/ui/button';
	import { chatManager } from '$lib/stores/globalStore';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	let { data, children } = $props();
	let conversations: ConversationDTO[] = $state([]);

	onMount(() => {
		console.log('Data:', data);

		conversations = data.conversations.map((conversation) => {
			return new ConversationDTO(
				conversation.id,
				conversation.title,
				conversation.messages,
				conversation.createdAt,
				conversation.updatedAt
			);
		});

		console.log('Conversations:', conversations);
	});

	const createConversation = async () => {
		await chatManager
			.createConversation()
			.then((response) => {
				console.log('Conversation created:', response);
			})
			.catch((error) => {
				console.error('Error creating conversation:', error);
			});
	};
</script>

<div class="grid h-screen grid-cols-[250px_1fr] grid-rows-[auto_1fr] overflow-hidden">
	<aside class="row-span-2 overflow-y-auto border-r border-gray-200 bg-gray-100 p-4">
		<Button variant="ghost" aria-label="Menu" class="w-full" on:click={createConversation}>
			New Conversation
		</Button>
		<nav>
			<ul class="space-y-4 text-gray-700">
				{#each conversations as conversation}
					<li>
						<Button variant="ghost" class="w-full" on:click={() => goto(`/${conversation.id}`)}>
							{conversation.title}
						</Button>
					</li>
				{/each}
			</ul>
		</nav>
	</aside>

	<header
		class="col-start-2 flex items-center justify-end space-x-4 border-b border-gray-200 bg-white p-4"
	>
		<!-- <Button variant="ghost" size="icon" aria-label="Search">
            <Search />
		</Button>
		<Button variant="ghost" size="icon" aria-label="Notifications">
            <Bell />
		</Button>
		<Button variant="ghost" size="icon" aria-label="User">
            <User />
		</Button> -->
	</header>

	<main class="col-start-2 flex flex-col overflow-hidden bg-white">
		{@render children()}
	</main>
</div>
