import type { ConversationDTO } from '$lib/DTO/Conversation';
import { Fetch } from '$lib/scripts/Fetch';
import { BACKEND_URL } from '$lib/stores/globalStore.js';
import { get } from 'svelte/store';

export async function load() {
	const url = `${get(BACKEND_URL)}/chat`;

	try {
		const response: ConversationDTO[] = await Fetch.get(url);

		return {
			conversations: response
		};
	} catch (error) {
		console.error('Error loading conversation:', error);
		throw new Error('Failed to load conversation');
	}
}
