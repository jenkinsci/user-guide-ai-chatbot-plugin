import ChatInput from "./ChatInput";
import { ChatTools } from "./ChatTools";

export default function ChatFooter({
  onSendMessage,
  inputValue,
  setInputValue,
}: {
  onSendMessage: (prompt: string) => void;
  inputValue: string;
  setInputValue: (s: string) => void;
}) {
  const onAttachContext = () => {};

  return (
    <div>
      <ChatTools onAttachContext={onAttachContext} currentPageName="Sample" />
      <ChatInput
        handleSendMessage={onSendMessage}
        inputValue={inputValue}
        setInputValue={setInputValue}
      />
    </div>
  );
}
