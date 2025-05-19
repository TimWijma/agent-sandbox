<script lang="ts">
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import type { ConversationDTO } from '$lib/DTO/Conversation';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';

	import { EllipsisVertical, Trash2 } from '@lucide/svelte';

	export let conversation: ConversationDTO;

	const openConversation = (conversationId: number) => {
		goto(`/${conversationId}`, { invalidateAll: true });
	};
</script>

<li>
	<Button
		variant="ghost"
		class="flex w-full items-center justify-between pr-0 hover:bg-gray-200"
		on:click={() => openConversation(conversation.id)}
	>
		<span class="text-left">{conversation.title}</span>
		<DropdownMenu.Root>
			<DropdownMenu.Trigger asChild let:builder>
				<Button builders={[builder]} variant="ghost" size="icon" class="hover:bg-gray-200">
					<EllipsisVertical />
				</Button>
			</DropdownMenu.Trigger>
			<DropdownMenu.Content>
				<DropdownMenu.Item>
					<Trash2 class="mr-2 h-4 w-4" />
					<span>Delete</span>
				</DropdownMenu.Item>
			</DropdownMenu.Content>
		</DropdownMenu.Root>
	</Button>
</li>
