import type { ConversationDTO } from '$lib/DTO/Conversation';
import { ChatManager } from '$lib/scripts/ChatManager';
import { writable, type Writable } from 'svelte/store';

export const BACKEND_URL = writable('http://localhost:8000');

export const conversations: Writable<ConversationDTO[]> = writable([]);

export const chatManager = new ChatManager('http://localhost:8000');
