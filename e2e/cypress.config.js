const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    setupNodeEvents(on, config) {},
    // Disable the support file requirement for now to avoid missing file errors
    supportFile: false,
    video: true,
    // Define the default timeout for elements to appear in Jenkins
    defaultCommandTimeout: 10000,
  },
});
