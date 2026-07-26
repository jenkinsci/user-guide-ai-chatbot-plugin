import ChatInput from "./ChatInput";
import { ChatTools } from "./ChatTools";

export default function ChatFooter({
  activeChatId,
  onSendMessage,
  onUploadContext,
  inputValue,
  setInputValue,
}: {
  activeChatId: number | null;
  onSendMessage: (prompt: string) => void;
  onUploadContext: () => Promise<boolean>;
  inputValue: string;
  setInputValue: (s: string) => void;
}) {
  const rootElement = document.getElementById("jenkins-ai-chatbot-root");
  const currentPageName =
    rootElement?.getAttribute("data-current-screen") || "";

  return (
    <div>
      <ChatTools
        activeChatId={activeChatId}
        onUploadContext={onUploadContext}
        currentPageName={currentPageName}
      />
      <ChatInput
        handleSendMessage={onSendMessage}
        inputValue={inputValue}
        setInputValue={setInputValue}
      />
    </div>
  );
}
