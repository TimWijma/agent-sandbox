import type { ConversationDTO } from '$lib/DTO/Conversation.js';
import { chatManager } from '$lib/stores/globalStore.js';

export async function load({ params }) {
	const { conversation_id } = params;

	try {
		const response: ConversationDTO = await chatManager.getConversation(conversation_id);

		return {
			conversation: response
		};
	} catch (error) {
		console.error('Error loading conversation:', error);
		throw new Error('Failed to load conversation');
	}
}
