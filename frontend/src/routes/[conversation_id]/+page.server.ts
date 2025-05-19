import { chatManager } from '$lib/stores/globalStore.js';

export async function load({ params }) {
	const { conversation_id } = params;

	try {
		const response = await chatManager.getConversation(conversation_id);

		return {
			conversation: {
				id: response.id,
				title: response.title,
				messages: response.messages,
				createdAt: response.created_at,
				updatedAt: response.updated_at
			}
		};
	} catch (error) {
		console.error('Error loading conversation:', error);
		throw new Error('Failed to load conversation');
	}
}
