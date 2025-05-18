export class Conversation {
	id: string;
	title: string;
	createdAt: Date;
	updatedAt: Date;

	constructor(id: string, title: string, createdAt: Date, updatedAt: Date) {
		this.id = id;
		this.title = title;
		this.createdAt = createdAt;
		this.updatedAt = updatedAt;
	}
}
