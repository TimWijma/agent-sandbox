import { Fetch } from './Fetch';

export class ChatManager {
	backendUrl: string;

	constructor(backendUrl: string) {
		this.backendUrl = backendUrl;
	}

	async getConversations(): Promise<any> {
		const url = `${this.backendUrl}/chat`;
		const response = await Fetch.get(url).catch((error) => {
			console.error('Error:', error);
			throw new Error('Failed to fetch conversations');
		});
		return response;
	}

	async getConversation(conversationId: string): Promise<any> {
		const url = `${this.backendUrl}/chat/${conversationId}`;
		const response = await Fetch.get(url).catch((error) => {
			console.error('Error:', error);
			throw new Error('Failed to fetch conversation');
		});
		return response;
	}

	async createConversation(): Promise<any> {
		const url = `${this.backendUrl}/chat`;

		const response = await Fetch.post(url).catch((error) => {
			console.error('Error:', error);
			throw new Error('Failed to create conversation');
		});

		return response;
	}

	async sendMessage(conversation_id: number, message: string): Promise<any> {
		const url = `${this.backendUrl}/chat/${conversation_id}/messages`;
		const body = JSON.stringify({ message });

		const response = await Fetch.post(url, body).catch((error) => {
			console.error('Error:', error);
			throw new Error('Failed to send message');
		});

		return response;
	}
}
