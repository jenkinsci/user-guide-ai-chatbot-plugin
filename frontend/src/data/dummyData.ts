import type { ChatMessage, Chat } from "../types/types";

export const DUMMY_SESSIONS: Chat[] = [
  {
    id: "session-1",
    title: "Build failed on main",
    updatedAt: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
  },
  {
    id: "session-2",
    title: "Install Docker plugin",
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
  },
  {
    id: "session-3",
    title: "Difference between pipeline and project",
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
  },
];

export const DUMMY_MESSAGES: Record<string, ChatMessage[]> = {
  "session-1": [
    {
      id: 1,
      sender: "user",
      text: "My build is failing on main, can you help me?",
      createdAt: new Date(Date.now() - 1000 * 60 * 16).toISOString(),
      updatedAt: null,
    },
    {
      id: 2,
      sender: "bot",
      text: "Sure! Can you share the error log with me? Usually, failures on main are related to dependency conflicts or failing tests.",
      createdAt: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      updatedAt: null,
    },
  ],
  "session-2": [
    {
      id: 3,
      sender: "user",
      text: "How do I install a new Docker plugin in Jenkins?",
      createdAt: new Date(Date.now() - 1000 * 60 * 61).toISOString(),
      updatedAt: null,
    },
    {
      id: 4,
      sender: "bot",
      text: "Go to Manage Jenkins > Plugins > Available plugins, search for 'Docker' and click on Install. Do you also need the Docker Pipeline plugin?",
      createdAt: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      updatedAt: null,
    },
    {
      id: 5,
      sender: "user",
      text: "Yes, I need that too.",
      createdAt: new Date(Date.now() - 1000 * 60 * 59).toISOString(),
      updatedAt: null,
    },
  ],
  "session-3": [
    {
      id: 6,
      sender: "user",
      text: "What is the difference between a pipeline and a project in Jenkins?",
      createdAt: new Date(
        Date.now() - 1000 * 60 * 60 * 24 * 2 - 1000 * 60,
      ).toISOString(),
      updatedAt: null,
    },
    {
      id: 7,
      sender: "bot",
      text: "A Project is a job configured via the UI with predefined steps, whereas a Pipeline is defined via code (Jenkinsfile), offering greater flexibility and versioning.",
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
      updatedAt: null,
    },
  ],
};
