Cypress.on("window:before:load", (win) => {
  cy.spy(win.console, "error").as("consoleError");
});

describe("Check Frontend UI injection correctness", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.get("#jenkins-ai-chatbot-root", { timeout: 15000 }).should("exist");
  });

  it("Should display the button, click it, and open the panel", () => {
    cy.get('[data-cy="open-chatbot"]', { timeout: 15000 })
      .should("exist")
      .click({ force: true });
  });
});

describe("Chat Interactions: Send, Edit, Retry Message and Upload Context", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.get("#jenkins-ai-chatbot-root", { timeout: 15000 }).should("exist");

    // Open panel
    cy.get('[data-cy="open-chatbot"]', { timeout: 15000 })
      .should("exist")
      .click({ force: true });
  });

  it("Should send a new message", () => {
    const promptText = "How do I trigger a Jenkins build?";

    // Send prompt
    cy.get('[data-cy="chat-input"]').type(promptText);
    cy.get('[data-cy="send-message"]').click();

    // Check answer is visible
    cy.contains(`Mocked response for prompt: ${promptText}`).should(
      "be.visible",
    );
  });

  it("Should edit an existing message", () => {
    const initialMessage = "Initial wrong message";
    const editedMessage = "Corrected message";

    // Send prompt
    cy.get('[data-cy="chat-input"]').type(initialMessage);
    cy.get('[data-cy="send-message"]').click();

    // Check answer is visible
    cy.contains(`Mocked response for prompt: ${initialMessage}`).should(
      "be.visible",
    );

    // Open edit message
    cy.get('[data-cy="edit-button"]').last().click({ force: true });

    // Write new prompt
    cy.get('[data-cy="edit-input"]')
      .last()
      .find("textarea:not([aria-hidden])")
      .clear()
      .type(editedMessage);

    // Confirm edit
    cy.get('[data-cy="confirm-edit-button"]').click();

    // Check answer is visible
    cy.contains(`Mocked response for prompt: ${editedMessage}`).should(
      "be.visible",
    );
  });

  it("Should retry a message", () => {
    const retryMessage = "Explain pipelines";

    // Send prompt
    cy.get('[data-cy="chat-input"]').type(retryMessage);
    cy.get('[data-cy="send-message"]').click();

    // Click retry
    cy.get('[data-cy="retry-button"]').last().click();

    // Check answer is visible
    cy.contains(`Mocked response for prompt: ${retryMessage}`).should(
      "be.visible",
    );
  });

  it("Should upload the current page context", () => {
    // Upload context
    cy.get('[data-cy="upload-context"]').click();

    // Check upload is succesfull
    cy.contains("Updated at", { timeout: 10000 }).should("be.visible");
  });
});

describe("Chat History Management", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.get("#jenkins-ai-chatbot-root", { timeout: 15000 }).should("exist");

    // Open panel
    cy.get('[data-cy="open-chatbot"]', { timeout: 15000 })
      .should("exist")
      .click({ force: true });

    // Open the history drawer before executing history actions
    cy.get('[data-cy="open-history-button"]').click();
  });

  it("Should create a new chat", () => {
    cy.get('[data-cy="create-chat-history-item"]').click();
  });

  it("Should edit a chat history title", () => {
    const newTitle = "Pipeline Configuration Chat";

    // Click Edit for the first history item
    cy.get('[data-cy="edit-chat-history-item-title"]')
      .first()
      .click({ force: true });

    // Write new title
    cy.get('[data-cy="edit-chat-history-item-title-input"]')
      .clear()
      .type(newTitle);

    // Confirm update
    cy.get('[data-cy="confirm-edit-chat-history-item-title"]').click();

    // Verify the new title is saved in the list
    cy.contains(newTitle).should("be.visible");
  });

  it("Should delete a chat history item", () => {
    // Click delete on the first item
    cy.get('[data-cy="delete-chat-history-item"]')
      .first()
      .click({ force: true });

    // Confirm the deletion
    cy.get('[data-cy="confirm-delete-chat-history-item"]').click();
  });
});
