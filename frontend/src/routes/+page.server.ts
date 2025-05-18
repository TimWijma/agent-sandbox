import { Conversation } from '$lib/DTO/Conversation.js';
import { Fetch } from '$lib/scripts/Fetch';
import { BACKEND_URL } from '$lib/stores/globalStore.js';
import { get } from 'svelte/store';

export async function load() {
	const url = `${get(BACKEND_URL)}/chat`;

	try {
		const response = await Fetch.get(url);
		console.log('Response:', response);

		return {
			conversations: response.map((conv) => {
				return {
					id: conv.id,
					title: conv.title,
					messages: conv.messages,
					createdAt: conv.created_at,
					updatedAt: conv.updated_at
				};
			})
		};
	} catch (error) {
		console.error('Error loading conversation:', error);
		throw new Error('Failed to load conversation');
	}
}
