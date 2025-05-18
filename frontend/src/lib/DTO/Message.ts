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

// export class MessageContent {
// 	type: MessageType;
// 	originalMessage: string;
// 	content: string;

// 	constructor(type: MessageType, originalText: string, result: string) {
// 		this.type = type;
// 		this.originalMessage = originalText;
// 		this.content = result;
// 	}
// }

export class Message {
	id: number;
	conversationId: number;
	content: string;
	type: MessageType;
	role: Role;
	createdAt: Date;
	originalMessage?: string;

	constructor(
		id: number,
		conversationId: number,
		content: string,
		type: MessageType,
		role: Role,
		createdAt: Date,
		originalMessage?: string
	) {
		this.id = id;
		this.conversationId = conversationId;
		this.content = content;
		this.type = type;
		this.role = role;
		this.createdAt = createdAt;
		this.originalMessage = originalMessage;
	}
}
