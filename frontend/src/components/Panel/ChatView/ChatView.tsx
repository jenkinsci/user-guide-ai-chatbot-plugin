import React, { useCallback, useEffect, useState } from "react";
import { ChatPlaceholder } from "./ChatPlaceholder/ChatPlaceholder";
import ChatContent from "./ChatContent/ChatContent";
import ChatFooter from "./ChatFooter/ChatFooter";
import { apiCall } from "../../../api/api";
import {
  ChatEntity,
  QAPairEntity,
  QuestionEntity,
} from "../../../models/models";
import ErrorBanner from "../../ErrorBanner";

interface ChatViewProps {
  activeChatId: number | null;
  onCreateChat: (chat: ChatEntity) => void;
}

const QA_PAIR_LIMIT = 10;

export default function ChatView({
  activeChatId,
  onCreateChat,
}: ChatViewProps) {
  const [messages, setMessages] = useState<QAPairEntity[]>([]);
  const [isBotAnswering, setIsBotAnswering] = useState<boolean>(false);
  const [inputValue, setInputValue] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [hasMoreOlder, setHasMoreOlder] = useState<boolean>(true);
  const [offset, setOffset] = useState<number>(0);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchMessages = useCallback(
    async (pairOffset: number) => {
      setLoading(true);

      try {
        const response = await apiCall({
          method: "GET",
          path: `chats/${activeChatId}?limit=${QA_PAIR_LIMIT}&offset=${pairOffset}`,
        });

        if (!response.ok) {
          throw new Error(`HTTP Error: ${response.status}`);
        }

        const data = await response.json();

        const newMessages = data["items"]
          .map(
            (el: {
              id: number;
              chat_id: number;
              created_at: string;
              question: { id: number; content: string; created_at: string };
              answer?: { id: number; content: string; created_at: string };
            }) => new QAPairEntity(el),
          )
          .reverse();

        if (newMessages.length < QA_PAIR_LIMIT) {
          setHasMoreOlder(false);
        }

        setOffset((old) => old + QA_PAIR_LIMIT);

        setMessages((old) => {
          const newState = [...newMessages, ...old];
          return newState;
        });
      } catch (error) {
        console.error("Failed to fetch older messages:", error);
        setErrorMessage("Failed to load chat history. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    [activeChatId],
  );

  const onLoadOlder = () => fetchMessages(offset);

  useEffect(() => {
    const initialFetch = async () => {
      setMessages([]);
      setOffset(0);
      setHasMoreOlder(true);
      await fetchMessages(0);
    };

    if (activeChatId && activeChatId !== messages[0]?.chatId) {
      initialFetch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeChatId]);

  const createChat = async (prompt: string) => {
    setHasMoreOlder(false);

    const response = await apiCall({
      method: "POST",
      path: "chats/",
      payload: {
        title: prompt.length > 80 ? prompt.slice(0, 80) + "..." : prompt,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }

    const data = await response.json();
    const newChat = new ChatEntity(data);

    onCreateChat(newChat);
    return newChat.id;
  };

  const onSendMessage = async (
    prompt: string,
    customRollbackState?: QAPairEntity[],
  ) => {
    if (!prompt.trim()) return;

    setInputValue("");
    setIsBotAnswering(true);
    setErrorMessage(null);

    let snapshot: QAPairEntity[] = [];

    setMessages((prev) => {
      snapshot = customRollbackState || [...prev];
      return prev;
    });

    try {
      let newChatId;
      if (!activeChatId) newChatId = await createChat(prompt);

      const chatId = newChatId || activeChatId;
      const tempQaId = Date.now();

      const optimisticQaPair = new QAPairEntity({
        id: tempQaId,
        chat_id: chatId!,
        created_at: new Date().toISOString(),
        question: {
          id: tempQaId,
          content: prompt,
          created_at: new Date().toISOString(),
        },
        answer: {
          id: tempQaId + 1,
          content: "",
          created_at: new Date().toISOString(),
        },
      });

      setMessages((prev) => [...prev, optimisticQaPair]);

      const response = await apiCall({
        method: "POST",
        path: "messages/send",
        payload: {
          chat_id: chatId,
          content: prompt,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("ReadableStream is not supported.");
      }

      const streamReader = response.body.getReader();
      const textDecoder = new TextDecoder("utf-8");

      let isStreamComplete = false;
      let actualQaPairId: number | null = null;
      let buffer = "";

      while (!isStreamComplete) {
        const { value, done } = await streamReader.read();
        isStreamComplete = done;

        if (value) {
          buffer += textDecoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (let line of lines) {
            line = line.trim();
            if (!line) continue;

            if (line.startsWith("data: ")) {
              line = line.replace(/^data:\s*/, "");
            }

            if (line === "[DONE]") continue;

            try {
              const data = JSON.parse(line);

              if (data["qa_pair_data"]) {
                actualQaPairId = data["qa_pair_data"];
              }

              const newContent: string = data["content"] || "";

              setMessages((prev) => {
                const updatedMessages = [...prev];
                const targetIndex = updatedMessages.length - 1;
                const oldMessage = updatedMessages[targetIndex];

                const updatedAnswer = oldMessage.answer
                  ? {
                      ...oldMessage.answer,
                      content: oldMessage.answer.content + newContent,
                    }
                  : undefined;

                updatedMessages[targetIndex] = Object.assign(
                  Object.create(Object.getPrototypeOf(oldMessage)),
                  oldMessage,
                  {
                    id:
                      actualQaPairId && oldMessage.id === tempQaId
                        ? actualQaPairId
                        : oldMessage.id,
                    answer: updatedAnswer,
                  },
                );

                return updatedMessages;
              });
            } catch (error) {
              console.warn("Failed to parse stream chunk:", line, error);
            }
          }
        }
      }
    } catch (error) {
      console.error("Error during message streaming:", error);

      setMessages(snapshot);

      setInputValue(prompt);

      setErrorMessage("Failed to send the message. Please try again.");
    } finally {
      setIsBotAnswering(false);
    }
  };

  const onEditMessage = async (question: QuestionEntity, newText: string) => {
    let snapshot: QAPairEntity[] = [];

    setMessages((prev) => {
      snapshot = [...prev];
      const targetIndex = prev.findIndex((m) => m.question.id === question.id);

      if (targetIndex === -1) return prev;
      return prev.slice(0, targetIndex);
    });

    await onSendMessage(newText, snapshot);
  };

  const onRetryMessage = async (question: QuestionEntity) => {
    let snapshot: QAPairEntity[] = [];

    setMessages((prev) => {
      snapshot = [...prev];
      const targetIndex = prev.findIndex((m) => m.question.id === question.id);

      if (targetIndex === -1) return prev;
      return prev.slice(0, targetIndex);
    });

    await onSendMessage(question.content, snapshot);
  };

  const onUploadContext = async () => {
    try {
      const response = await apiCall({
        method: "POST",
        path: `context/${activeChatId}`,
        payload: {},
      });
      console.log(response);
    } catch (error) {
      console.log(error);
      setErrorMessage("Failed to upload context. Please try again.");
      return false;
    }
    
    return true;
  };

  const handleCloseError = () => {
    setErrorMessage(null);
  };

  const isBotReasoning =
    isBotAnswering &&
    messages[messages.length - 1]?.answer?.content?.length === 0;

  return (
    <>
      {!activeChatId ? (
        <ChatPlaceholder
          onSuggestionClick={(prompt) => onSendMessage(prompt)}
        />
      ) : (
        <ChatContent
          key={activeChatId}
          messages={messages}
          isBotReasoning={isBotReasoning}
          onEditMessage={onEditMessage}
          onRetryMessage={onRetryMessage}
          isLoadingOlder={loading}
          hasMoreOlder={hasMoreOlder}
          onLoadOlder={onLoadOlder}
        />
      )}
      <ChatFooter
        onSendMessage={(prompt) => onSendMessage(prompt)}
        onUploadContext={onUploadContext}
        inputValue={inputValue}
        setInputValue={setInputValue}
      />

      <ErrorBanner message={errorMessage} handleCloseError={handleCloseError} />
    </>
  );
}
