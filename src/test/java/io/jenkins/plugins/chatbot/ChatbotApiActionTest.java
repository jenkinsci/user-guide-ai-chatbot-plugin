package io.jenkins.plugins.chatbot;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import com.cloudbees.plugins.credentials.CredentialsScope;
import com.cloudbees.plugins.credentials.SystemCredentialsProvider;
import hudson.FilePath;
import hudson.Launcher;
import hudson.model.AbstractBuild;
import hudson.model.BuildListener;
import hudson.model.FreeStyleProject;
import hudson.util.Secret;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;
import net.sf.json.JSONObject;
import org.htmlunit.WebResponse;
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl;
import org.junit.jupiter.api.Test;
import org.jvnet.hudson.test.JenkinsRule;
import org.jvnet.hudson.test.TestBuilder;
import org.jvnet.hudson.test.junit.jupiter.WithJenkins;

@WithJenkins
class ChatbotApiActionTest {

    private static final String SECRET = "0123456789qwertyuiop0123456789abcdef";
    private static final String ISSUER = "fastapi-backend";

    @Test
    void rejectsMissingOrBadToken(JenkinsRule j) throws Exception {
        configureSecret();
        Date inOneMinute = new Date(System.currentTimeMillis() + 60_000);
        Date oneMinuteAgo = new Date(System.currentTimeMillis() - 60_000);

        assertEquals(200, statusFor(j, token(SECRET, ISSUER, inOneMinute)));

        assertEquals(401, statusFor(j, null));
        assertEquals(401, statusFor(j, "Basic abc"));
        assertEquals(401, statusFor(j, token("some-other-secret-that-is-32-chars!", ISSUER, inOneMinute)));
        assertEquals(401, statusFor(j, token(SECRET, "jenkins-chatbot-proxy", inOneMinute)));
        assertEquals(401, statusFor(j, token(SECRET, ISSUER, oneMinuteAgo)));
    }

    @Test
    void rejectsUnsafePaths(JenkinsRule j) throws Exception {
        configureSecret();

        for (String path : List.of("../x", "a/../../x", "/etc/passwd", "\\x", "C:\\x")) {
            JSONObject result = readFile(j, "app", 1, "ws-default", path);
            assertEquals("error", result.getString("status"), path);
            assertTrue(result.getString("message").contains("Path traversal is not allowed"), path);
        }

        assertEquals(
                "File path cannot be empty.",
                readFile(j, "app", 1, "ws-default", "").getString("message"));
    }

    @Test
    void readsWorkspaceFile(JenkinsRule j) throws Exception {
        configureSecret();
        buildJobWithWorkspace(j);

        JSONObject result = readFile(j, "app", 1, "ws-default", "src/App.java");

        assertEquals("success", result.getString("status"));
        assertEquals("class App {}", result.getString("content"));
    }

    @Test
    void workspaceTreeSkipsHeavyFolders(JenkinsRule j) throws Exception {
        configureSecret();
        buildJobWithWorkspace(j);

        String tree =
                get(j, "workspaceTree?jobName=app&buildNumber=1", validToken()).getContentAsString();

        assertTrue(tree.contains("App.java"));
        assertFalse(tree.contains(".git"));
        assertFalse(tree.contains("node_modules"));
        assertFalse(tree.contains("target"));
    }

    @Test
    void truncatesLargeFiles(JenkinsRule j) throws Exception {
        configureSecret();
        buildJobWithWorkspace(j);

        String content = readFile(j, "app", 1, "ws-default", "big.txt").getString("content");

        assertTrue(content.endsWith("[FILE TRUNCATED]"));
        assertTrue(content.length() < 60_000);
    }

    @Test
    void unknownJobBuildOrWorkspace(JenkinsRule j) throws Exception {
        configureSecret();
        buildJobWithWorkspace(j);

        assertEquals(
                "Job or Build not found.",
                readFile(j, "missing", 1, "ws-default", "src/App.java").getString("message"));
        assertEquals(
                "Job or Build not found.",
                readFile(j, "app", 99, "ws-default", "src/App.java").getString("message"));
        assertEquals(
                "Invalid or missing Workspace ID.",
                readFile(j, "app", 1, "wrong-id", "src/App.java").getString("message"));
    }

    private static void configureSecret() {
        SystemCredentialsProvider.getInstance()
                .getCredentials()
                .add(new StringCredentialsImpl(
                        CredentialsScope.GLOBAL, "jwt-secret", "JWT secret", Secret.fromString(SECRET)));
        ChatbotGlobalConfig.get().setJwtSecretId("jwt-secret");
    }

    // A freestyle job "app" whose build #1 writes a few files into its workspace
    private static void buildJobWithWorkspace(JenkinsRule j) throws Exception {
        FreeStyleProject project = j.createFreeStyleProject("app");
        project.getBuildersList().add(new TestBuilder() {
            @Override
            public boolean perform(AbstractBuild<?, ?> build, Launcher launcher, BuildListener listener)
                    throws InterruptedException, java.io.IOException {
                FilePath workspace = build.getWorkspace();
                workspace.child("src/App.java").write("class App {}", "UTF-8");
                workspace.child("big.txt").write("a".repeat(60_000), "UTF-8");
                workspace.child("node_modules/lib.js").write("x", "UTF-8");
                workspace.child(".git/HEAD").write("x", "UTF-8");
                workspace.child("target/App.class").write("x", "UTF-8");
                return true;
            }
        });
        j.buildAndAssertSuccess(project);
    }

    private static String token(String secret, String issuer, Date expiresAt) {
        return "Bearer "
                + JWT.create().withIssuer(issuer).withExpiresAt(expiresAt).sign(Algorithm.HMAC256(secret));
    }

    private static String validToken() {
        return token(SECRET, ISSUER, new Date(System.currentTimeMillis() + 60_000));
    }

    private static JSONObject readFile(JenkinsRule j, String jobName, int buildNumber, String workspaceId, String path)
            throws Exception {
        String query = "workspaceFile?jobName=" + jobName + "&buildNumber=" + buildNumber + "&workspaceId="
                + workspaceId + "&filePath=" + URLEncoder.encode(path, StandardCharsets.UTF_8);
        return JSONObject.fromObject(get(j, query, validToken()).getContentAsString());
    }

    private static int statusFor(JenkinsRule j, String authHeader) throws Exception {
        return get(j, "workspaceTree?jobName=app&buildNumber=1", authHeader).getStatusCode();
    }

    private static WebResponse get(JenkinsRule j, String endpoint, String authHeader) throws Exception {
        JenkinsRule.WebClient webClient = j.createWebClient();
        webClient.getOptions().setJavaScriptEnabled(false);
        webClient.getOptions().setThrowExceptionOnFailingStatusCode(false);
        if (authHeader != null) {
            webClient.addRequestHeader("Authorization", authHeader);
        }
        return webClient.goTo("chatbot-api/" + endpoint, null).getWebResponse();
    }
}
