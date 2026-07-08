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
  return (
    <div>
      <ChatTools onUploadContext={onUploadContext} currentPageName="Sample" />
      <ChatInput
        handleSendMessage={onSendMessage}
        inputValue={inputValue}
        setInputValue={setInputValue}
      />
    </div>
  );
}
