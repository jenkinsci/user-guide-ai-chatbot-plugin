package io.jenkins.plugins.chatbot;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.cloudbees.plugins.credentials.CredentialsScope;
import com.cloudbees.plugins.credentials.SystemCredentialsProvider;
import hudson.model.User;
import hudson.security.ACL;
import hudson.security.ACLContext;
import hudson.util.ListBoxModel;
import hudson.util.Secret;
import jenkins.model.Jenkins;
import org.htmlunit.html.HtmlForm;
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl;
import org.junit.jupiter.api.Test;
import org.jvnet.hudson.test.JenkinsRule;
import org.jvnet.hudson.test.MockAuthorizationStrategy;
import org.jvnet.hudson.test.junit.jupiter.WithJenkins;

@WithJenkins
class ChatbotGlobalConfigTest {

    @Test
    void configRoundTrip(JenkinsRule j) throws Exception {
        addJwtSecret();
        ChatbotGlobalConfig config = ChatbotGlobalConfig.get();
        config.setBackendUrl("http://localhost:8000/");
        config.setJwtSecretId("jwt-secret");

        JenkinsRule.WebClient webClient = j.createWebClient();
        webClient.getOptions().setThrowExceptionOnScriptError(false);
        HtmlForm form = webClient.goTo("configure").getFormByName("config");
        j.submit(form);
        assertEquals("http://localhost:8000/", ChatbotGlobalConfig.get().getBackendUrl());
        assertEquals("jwt-secret", ChatbotGlobalConfig.get().getJwtSecretId());
    }

    @Test
    void secretListForAdminVsUser(JenkinsRule j) {
        addJwtSecret();
        j.jenkins.setSecurityRealm(j.createDummySecurityRealm());
        j.jenkins.setAuthorizationStrategy(new MockAuthorizationStrategy()
                .grant(Jenkins.ADMINISTER)
                .everywhere()
                .to("admin")
                .grant(Jenkins.READ)
                .everywhere()
                .to("user"));

        ChatbotGlobalConfig chatBotConfig = ChatbotGlobalConfig.get();

        try (ACLContext ignored = ACL.as2(User.getById("admin", true).impersonate2())) {
            ListBoxModel items = chatBotConfig.doFillJwtSecretIdItems("");
            assertTrue(items.stream().anyMatch(option -> option.value.equals("jwt-secret")));
        }
        try (ACLContext ignored = ACL.as2(User.getById("user", true).impersonate2())) {
            ListBoxModel items = chatBotConfig.doFillJwtSecretIdItems("current-id");
            assertFalse(items.stream().anyMatch(option -> option.value.equals("jwt-secret")));
            assertTrue(items.stream().anyMatch(option -> option.value.equals("current-id")));
        }
    }

    private static void addJwtSecret() {
        SystemCredentialsProvider.getInstance()
                .getCredentials()
                .add(new StringCredentialsImpl(
                        CredentialsScope.GLOBAL,
                        "jwt-secret",
                        "JWT secret",
                        Secret.fromString("my-secret-key-for-chatbot-tests")));
    }
}
