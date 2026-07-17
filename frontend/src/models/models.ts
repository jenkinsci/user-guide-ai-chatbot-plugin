export class ChatEntity {
  id: number;
  userId: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;

  constructor(data: {
    id: number;
    user_id: string;
    title: string;
    created_at: string;
    updated_at: string;
  }) {
    this.id = data.id;
    this.userId = data.user_id;
    this.title = data.title;
    this.createdAt = new Date(data.created_at);
    this.updatedAt = new Date(data.updated_at);
  }
}

export class QAPairEntity {
  id: number;
  chatId: number;
  createdAt: Date;
  question: QuestionEntity;
  answer?: AnswerEntity;

  constructor(data: {
    id: number;
    chat_id: number;
    created_at: string;
    question: {
      id: number;
      content: string;
      created_at: string;
    };
    answer?: {
      id: number;
      content: string;
      created_at: string;
    };
  }) {
    this.id = data.id;
    this.chatId = data.chat_id;
    this.createdAt = new Date(data.created_at);
    this.question = new QuestionEntity(data.question);
    if (data.answer) this.answer = new AnswerEntity(data.answer);
  }
}

class MessageEntity {
  id: number;
  content: string;
  createdAt: Date;

  constructor(data: { id: number; content: string; created_at: string }) {
    this.id = data.id;
    this.content = data.content;
    this.createdAt = new Date(data.created_at);
  }
}

export class QuestionEntity extends MessageEntity {}
export class AnswerEntity extends MessageEntity {}
