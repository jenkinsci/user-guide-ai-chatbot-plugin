export interface ChatMessage {
  id: number;
  sender: "user" | "bot";
  text: string;
  createdAt: string;
  updatedAt: string | null;
}

export interface Chat {
  id: string;
  title: string;
  updatedAt: string;
}
