import { Conversation } from '$lib/DTO/Conversation.js';
import { Fetch } from '$lib/scripts/Fetch';
import { BACKEND_URL } from '$lib/stores/globalStore.js';
import { get } from 'svelte/store';

export async function load({ params }) {
	const { conversation_id } = params;

	const url = `${get(BACKEND_URL)}/chat/${conversation_id}`;

	try {
		const response = await Fetch.get(url);

		return {
			conversation: {
				id: response.id,
				name: response.name,
				messages: response.messages,
				created_at: response.created_at,
				updated_at: response.updated_at
			}
		};
	} catch (error) {
		console.error('Error loading conversation:', error);
		throw new Error('Failed to load conversation');
	}
}
