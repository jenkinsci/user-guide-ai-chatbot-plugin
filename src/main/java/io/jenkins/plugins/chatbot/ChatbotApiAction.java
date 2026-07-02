package io.jenkins.plugins.chatbot;

import com.cloudbees.plugins.credentials.CredentialsMatchers;
import com.cloudbees.plugins.credentials.domains.URIRequirementBuilder;
import hudson.Extension;
import hudson.model.RootAction;
import org.kohsuke.stapler.StaplerRequest2;
import org.kohsuke.stapler.StaplerResponse2;
import jenkins.model.Jenkins;
import com.cloudbees.plugins.credentials.CredentialsProvider;
import org.jenkinsci.plugins.plaincredentials.StringCredentials;
import hudson.security.ACL;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Date;
import java.util.Set;

@Extension
public class ChatbotApiAction implements RootAction {

    final private String BASE_URL = "chatbot-api";

    @Override
    public String getIconFileName() {
        return null; 
    }

    @Override
    public String getDisplayName() {
        return null;
    }

    @Override
    public String getUrlName() {
        return BASE_URL;
    }

    private StringCredentials getCredentials(ChatbotGlobalConfig pluginConfig){
        String storedSecretId = pluginConfig.getJwtSecretId();

        if (storedSecretId == null) return null;

        return CredentialsMatchers.firstOrNull(
                CredentialsProvider.lookupCredentialsInItemGroup(
                        StringCredentials.class,
                        Jenkins.get(),
                        ACL.SYSTEM2,
                        URIRequirementBuilder.create().build()
                ),
                CredentialsMatchers.withId(storedSecretId)
        );
    }

    private String generateToken(String secret, long ttl){
        Algorithm signingAlgorithm = Algorithm.HMAC256(secret);

        return JWT.create()
                .withIssuer("jenkins-chatbot-proxy")
                .withClaim("sub", Jenkins.getAuthentication2().getName())
                .withIssuedAt(new Date())
                .withExpiresAt(new Date(System.currentTimeMillis() + ttl))
                .sign(signingAlgorithm);
    }

    /**
     * Intercepts all requests matching /chatbot-api/* and acts as a proxy.
     */
    public void doDynamic(StaplerRequest2 request, StaplerResponse2 response) throws Exception {

        Jenkins.get().checkPermission(Jenkins.READ);
        
        // Get Backend URL
        ChatbotGlobalConfig pluginConfig = ChatbotGlobalConfig.get();

        String targetBackendUrl = pluginConfig.getBackendUrl();

        if (targetBackendUrl == null) {
            response.sendError(500, "Backend Url value is missing in Jenkins Global Settings.");
            return;
        }

        // Get Secret Key
        StringCredentials credentials = getCredentials(pluginConfig);

        if (credentials == null) {
            response.sendError(500, "Configured JWT Secret ID could not be found.");
            return;
        }

        String rawSecret = credentials.getSecret().getPlainText();
        String generatedToken = generateToken(rawSecret, 3600000);

        // Extract the path requested by the client and construct the downstream URL
        String dynamicPath = request.getRestOfPath();
        String targetEndpointString = targetBackendUrl
                + (targetBackendUrl.endsWith("/") ? "" : "/")
                + (dynamicPath.startsWith("/") ? dynamicPath.substring(1) : dynamicPath);

        String incomingQueryString = request.getQueryString();
        if (incomingQueryString != null && !incomingQueryString.isEmpty()) {
            targetEndpointString += "?" + incomingQueryString;
        }

        URL targetEndpoint = new URL(targetEndpointString);
        HttpURLConnection proxyConnection = (HttpURLConnection) targetEndpoint.openConnection();

        proxyConnection.setRequestMethod(request.getMethod());
        proxyConnection.setRequestProperty("Authorization", "Bearer " + generatedToken);

        if (request.getContentType() != null) {
            proxyConnection.setRequestProperty("Content-Type", request.getContentType());
        }

        Set<String> stateChangingMethods = Set.of("POST", "PUT", "PATCH", "DELETE");

        String currentMethod = request.getMethod().toUpperCase();

        if (stateChangingMethods.contains(currentMethod)) {
            proxyConnection.setDoOutput(true);
            try (InputStream clientRequestStream = request.getInputStream();
                 OutputStream downstreamStream = proxyConnection.getOutputStream()) {
                clientRequestStream.transferTo(downstreamStream);
            }
        }

        // Capture the response from the downstream backend
        int downstreamResponseCode = proxyConnection.getResponseCode();
        response.setStatus(downstreamResponseCode);

        String downstreamContentType = proxyConnection.getContentType();
        if (downstreamContentType != null) {
            response.setContentType(downstreamContentType);
        }

        // Determine if the backend is returning a Server-Sent Events stream
        boolean isServerSentEvents = downstreamContentType != null &&
                downstreamContentType.toLowerCase().contains("text/event-stream");

        if (isServerSentEvents) {
            // Prevent the browser and intermediate proxies from buffering the stream
            response.setHeader("Cache-Control", "no-cache");
            response.setHeader("Connection", "keep-alive");
        }

        // Return the payload back to the originating client
        try (InputStream downstreamResponseStream = (downstreamResponseCode >= 200 && downstreamResponseCode < 300)
                ? proxyConnection.getInputStream() : proxyConnection.getErrorStream();
             OutputStream clientOutputStream = response.getOutputStream()) {

            if (downstreamResponseStream != null) {
                if (isServerSentEvents) {
                    // Manual chunk reading and immediate flushing for SSE
                    byte[] streamBuffer = new byte[1024];
                    int bytesRead;

                    while ((bytesRead = downstreamResponseStream.read(streamBuffer)) != -1) {
                        clientOutputStream.write(streamBuffer, 0, bytesRead);
                        clientOutputStream.flush();
                    }
                } else {
                    // Standard bulk transfer for traditional REST/JSON responses
                    downstreamResponseStream.transferTo(clientOutputStream);
                }
            }
        }

        proxyConnection.disconnect();
    }
}