import ChatInput from "./ChatInput";
import { ChatTools } from "./ChatTools";

export default function ChatFooter({
  onSendMessage,
  onUploadContext,
  inputValue,
  setInputValue,
}: {
  onSendMessage: (prompt: string) => void;
  onUploadContext: () => Promise<boolean>;
  inputValue: string;
  setInputValue: (s: string) => void;
}) {
  const rootElement = document.getElementById("jenkins-ai-chatbot-root");
  const currentPageName =
    rootElement?.getAttribute("data-current-screen") || "";

  console.log("ROOT: " + rootElement);
  console.log("PG: " + currentPageName);

  return (
    <div>
      <ChatTools
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
