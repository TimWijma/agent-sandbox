<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	// import { Icon } from 'lucide-svelte';
	import { Search, Bell, User } from '@lucide/svelte';
	import { ChatManager } from '$lib/scripts/ChatManager';
	import { onMount } from 'svelte';
	import Message from '$lib/components/Message.svelte';

	const chatManager = new ChatManager('http://localhost:8000');

	let messages: {
		role: 'user' | 'model';
		message: string;
		type: 'general' | 'calculator' | 'file';
	}[] = [];
	let newMessage = '';

	const sendMessage = async () => {
		if (newMessage.trim() === '') return;

		messages = [
			...messages,
			{
				role: 'user',
				message: newMessage,
				type: 'general'
			}
		];
		let message = newMessage;
		newMessage = '';

		await chatManager
			.sendMessage(message)
			.then((response) => {
				messages = [...messages, response];
			})
			.catch((error) => {
				console.error('Error sending message:', error);
			});
	};

	onMount(async () => {
		messages = await chatManager.getMessages();
	});
</script>

<div class="grid h-screen grid-cols-[250px_1fr] grid-rows-[auto_1fr] overflow-hidden">
	<aside class="row-span-2 overflow-y-auto border-r border-gray-200 bg-gray-100 p-4">
		<nav>
			<ul class="space-y-4"></ul>
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
		<div class="flex-1 space-y-4 overflow-y-auto p-4">
			{#each messages as message}
				<Message {message} />
			{/each}
		</div>
		<div class="flex items-center border-t border-gray-200 p-4">
			<Input bind:value={newMessage} placeholder="Type your message here..." />
			<Button class="ml-2" on:click={sendMessage}>Send</Button>
		</div>
	</main>
</div>
