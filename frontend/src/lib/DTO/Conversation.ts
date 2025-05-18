import { Message } from './Message';

export class Conversation {
	id: number;
	title: string;
	messages: Message[];
	createdAt: Date;
	updatedAt: Date;

	constructor(id: number, title: string, messages: Message[], createdAt: Date, updatedAt: Date) {
		this.id = id;
		this.title = title;
		this.messages = messages;
		this.createdAt = createdAt;
		this.updatedAt = updatedAt;
	}
}
