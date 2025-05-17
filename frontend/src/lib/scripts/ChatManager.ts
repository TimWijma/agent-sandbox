import { Fetch } from './Fetch';

export class ChatManager {
	backendUrl: string;

	constructor(backendUrl: string) {
		this.backendUrl = backendUrl;
	}

	async sendMessage(message: string): Promise<any> {
		const url = `${this.backendUrl}/chat`;
		const body = JSON.stringify({ message });

		const response = await Fetch.post(url, body).catch((error) => {
			console.error('Error:', error);
			throw new Error('Failed to send message');
		});

		return response;
	}
}
