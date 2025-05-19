<script lang="ts">
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import type { ConversationDTO } from '$lib/DTO/Conversation';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';

	import { EllipsisVertical, Trash2 } from '@lucide/svelte';
	import { chatManager, conversations } from '$lib/stores/globalStore';
	import { page } from '$app/state';

	export let conversation: ConversationDTO;

	const openConversation = () => {
		goto(`/${conversation.id}`, { invalidateAll: true });
	};

	const deleteConversation = async () => {
		await chatManager
			.deleteConversation(conversation.id)
			.then(() => {
				$conversations = $conversations.filter((c) => c.id !== conversation.id);

				let currentId = parseInt(page.params.conversation_id);
				if (conversation.id === currentId) {
					goto('/', { invalidateAll: true });
				}
			})
			.catch((error) => {
				console.error('Error deleting conversation:', error);
			});
	};
</script>

<li>
	<Button
		variant="ghost"
		class="flex w-full items-center justify-between pr-0 hover:bg-gray-200"
		on:click={openConversation}
	>
		<span class="text-left">{conversation.title}</span>
		<DropdownMenu.Root>
			<DropdownMenu.Trigger asChild let:builder>
				<Button
					builders={[builder]}
					variant="ghost"
					size="icon"
					class="hover:bg-gray-200"
					on:click={(e) => e.stopPropagation()}
				>
					<EllipsisVertical />
				</Button>
			</DropdownMenu.Trigger>
			<DropdownMenu.Content>
				<DropdownMenu.Item on:click={deleteConversation}>
					<Trash2 class="mr-2 h-4 w-4" />
					<span>Delete</span>
				</DropdownMenu.Item>
			</DropdownMenu.Content>
		</DropdownMenu.Root>
	</Button>
</li>
