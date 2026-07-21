import React, { useEffect, useRef, useLayoutEffect, useState } from "react";
import { Stack, Box, CircularProgress } from "@mui/material";
import type { QAPairEntity, QuestionEntity } from "../../../../models/models";
import Message from "./Message/Message";
import { customScrollbar } from "../../../../theme/scrollBarStyles";
import TypingIndicator from "./TypingIndicator";
import DateBadge from "./DateBadge";

const formatGroupDate = (dateString: string | Date) => {
  const d = new Date(dateString);
  return d.toLocaleDateString("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
};

export default function ChatContent({
  messages,
  isBotReasoning,
  onEditMessage,
  onRetryMessage,
  onLoadOlder,
  isLoadingOlder = false,
  hasMoreOlder = false,
}: {
  messages: QAPairEntity[];
  isBotReasoning: boolean;
  onEditMessage: (m: QuestionEntity, newText: string) => void;
  onRetryMessage: (m: QuestionEntity) => void;
  onLoadOlder: () => void;
  isLoadingOlder?: boolean;
  hasMoreOlder?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const distanceFromBottomRef = useRef<number | null>(null);

  const wasEmptyRef = useRef(true);

  const [visibleDate, setVisibleDate] = useState<string | null>(null);
  const [isDateBadgeVisible, setIsDateBadgeVisible] = useState(false);
  const scrollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const editVisibleDate = async () => {
      setVisibleDate(formatGroupDate(messages[0].createdAt));
    };

    if (!visibleDate && messages.length > 0) {
      editVisibleDate();
    }
  }, [messages, visibleDate]);

  const handleScroll = () => {
    const container = containerRef.current;
    if (!container) return;

    if (container.scrollTop <= 5 && hasMoreOlder && !isLoadingOlder) {
      distanceFromBottomRef.current =
        container.scrollHeight - container.scrollTop;
      onLoadOlder();
    }

    const messageGroups = container.querySelectorAll(".qa-pair-group");
    let topVisibleGroup: Element | null = null;

    for (let i = 0; i < messageGroups.length; i++) {
      const el = messageGroups[i] as HTMLElement;
      if (el.offsetTop - container.offsetTop <= container.scrollTop + 80) {
        topVisibleGroup = el;
      } else {
        break;
      }
    }

    if (topVisibleGroup) {
      const currentGroupDate = topVisibleGroup.getAttribute("data-date");
      if (currentGroupDate && currentGroupDate !== visibleDate) {
        setVisibleDate(currentGroupDate);
      }
    }

    setIsDateBadgeVisible(true);
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    scrollTimeoutRef.current = setTimeout(() => {
      setIsDateBadgeVisible(false);
    }, 1500);
  };

  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container || distanceFromBottomRef.current === null) return;

    container.scrollTop =
      container.scrollHeight - distanceFromBottomRef.current;

    if (!isLoadingOlder) {
      distanceFromBottomRef.current = null;
    }
  }, [messages, isLoadingOlder]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (messages.length === 0) {
      wasEmptyRef.current = true;
      return;
    }

    if (wasEmptyRef.current && messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
      wasEmptyRef.current = false;
      return;
    }

    const isNearBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight <
      250;

    if (isBotReasoning || isNearBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isBotReasoning]);

  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
    };
  }, []);

  const onEditConfirm = (message: QuestionEntity, newText: string) => {
    onEditMessage(message, newText);
  };

  const onRetry = (message: QuestionEntity) => {
    onRetryMessage(message);
  };

  return (
    <Box
      sx={{
        flex: 1,
        position: "relative",
        display: "flex",
        overflow: "hidden",
      }}
    >
      <DateBadge
        isDateBadgeVisible={isDateBadgeVisible}
        visibleDate={visibleDate}
      />
      <Stack
        ref={containerRef}
        onScroll={handleScroll}
        spacing={2}
        sx={(theme) => ({
          flex: 1,
          overflowY: "auto",
          scrollbarGutter: "stable",
          p: 2,
          overflowAnchor: "none",
          transition: theme.transitions.create("background-color"),
          ...customScrollbar(theme),
        })}
      >
        {isLoadingOlder && (
          <Box sx={{ display: "flex", justifyContent: "center", p: 1 }}>
            <CircularProgress size={24} />
          </Box>
        )}

        {messages.length === 0 && !isLoadingOlder && !isBotReasoning ? (
          <div>No messages</div>
        ) : (
          messages.map((m) => (
            <Box
              key={`qa-pair-${m.id}`}
              className="qa-pair-group"
              data-date={formatGroupDate(m.createdAt)}
              sx={{ display: "flex", flexDirection: "column", gap: 2 }}
            >
              {m.question && (
                <Message
                  key={`question-${m.question.id}`}
                  message={m.question}
                  onEditConfirm={onEditConfirm}
                />
              )}
              {m.answer && m.answer.content.length > 0 && (
                <Message
                  key={`answer-${m.answer.id}`}
                  message={m.answer}
                  onRetry={() => onRetry(m.question!)}
                />
              )}
            </Box>
          ))
        )}

        {isBotReasoning && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </Stack>
    </Box>
  );
}
