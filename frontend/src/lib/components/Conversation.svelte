<script lang="ts">
	import Message from '$lib/components/Message.svelte';
	import { Message as MessageDTO, MessageType, Role } from '$lib/DTO/Message';
	import type { ConversationDTO } from '$lib/DTO/Conversation';
	import { chatManager } from '$lib/stores/globalStore';
	import { Button } from './ui/button';
	import { Input } from './ui/input';
	import { SendHorizontal } from '@lucide/svelte';

	export let conversation: ConversationDTO;
	let messages = conversation.messages;

	let newMessage = '';

	const sendMessage = async () => {
		if (newMessage.trim() === '') return;

		let message = newMessage;
		newMessage = '';

		let userMessage = new MessageDTO(
			-1,
			conversation.id,
			message,
			MessageType.General,
			Role.User,
			new Date()
		);
		messages = [...messages, userMessage];

		await chatManager
			.sendMessage(conversation.id, message)
			.then((response) => {
				messages = [...messages, response];
			})
			.catch((error) => {
				console.error('Error sending message:', error);
			});
	};
</script>

<div class="flex-1 space-y-4 overflow-y-auto p-4">
	{#each messages as message}
		<Message {message} />
	{/each}
</div>

<div class="flex items-center border-t border-gray-200 p-4">
	<Input bind:value={newMessage} placeholder="Type your message here..." />
	<Button class="ml-2" on:click={sendMessage}>
		Send
		<SendHorizontal class="ml-2" />
	</Button>
</div>
