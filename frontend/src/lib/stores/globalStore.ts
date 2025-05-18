import { ChatManager } from '$lib/scripts/ChatManager';
import { writable } from 'svelte/store';

export const BACKEND_URL = writable('http://localhost:8000');

export const chatManager = new ChatManager('http://localhost:8000');
