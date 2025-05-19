export enum MessageType {
	General = 'general',
	Calculator = 'calculator',
	File = 'file',
	Code = 'code'
}

export enum Role {
	User = 'user',
	Model = 'model'
}

export class Message {
	id: number;
	conversation_id: number;
	content: string;
	type: MessageType;
	role: Role;
	created_at: Date;
	original_message?: string;

	constructor(
		id: number,
		conversation_id: number,
		content: string,
		type: MessageType,
		role: Role,
		created_at: Date,
		original_message?: string
	) {
		this.id = id;
		this.conversation_id = conversation_id;
		this.content = content;
		this.type = type;
		this.role = role;
		this.created_at = created_at;
		this.original_message = original_message;
	}
}
