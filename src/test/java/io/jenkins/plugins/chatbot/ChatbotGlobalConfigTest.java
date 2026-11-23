package io.jenkins.plugins.chatbot;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.cloudbees.plugins.credentials.CredentialsScope;
import com.cloudbees.plugins.credentials.SystemCredentialsProvider;
import hudson.util.Secret;
import org.htmlunit.html.HtmlForm;
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl;
import org.junit.jupiter.api.Test;
import org.jvnet.hudson.test.JenkinsRule;
import org.jvnet.hudson.test.junit.jupiter.WithJenkins;

@WithJenkins
public class ChatbotGlobalConfigTest {

    @Test
    void configRoundTrip(JenkinsRule j) throws Exception {
        SystemCredentialsProvider.getInstance()
                .getCredentials()
                .add(new StringCredentialsImpl(
                        CredentialsScope.GLOBAL, "jwt-secret", "JWT secret", Secret.fromString("test-secret")));
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
}
