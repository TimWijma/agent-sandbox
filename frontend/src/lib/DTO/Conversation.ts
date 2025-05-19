import { MessageDTO } from './Message';

export class ConversationDTO {
	id: number;
	title: string;
	messages: MessageDTO[];
	created_at: Date;
	updated_at: Date;

	constructor(
		id: number,
		title: string,
		messages: MessageDTO[],
		created_at: Date,
		updated_at: Date
	) {
		this.id = id;
		this.title = title;
		this.messages = messages;
		this.created_at = created_at;
		this.updated_at = updated_at;
	}
}
