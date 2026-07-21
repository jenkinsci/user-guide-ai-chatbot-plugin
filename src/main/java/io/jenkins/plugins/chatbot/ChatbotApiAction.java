package io.jenkins.plugins.chatbot;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import com.cloudbees.plugins.credentials.CredentialsMatchers;
import com.cloudbees.plugins.credentials.CredentialsProvider;
import com.cloudbees.plugins.credentials.domains.URIRequirementBuilder;
import hudson.Extension;
import hudson.model.*;
import hudson.scm.ChangeLogSet;
import hudson.scm.ChangeLogSet.Entry;
import hudson.security.ACL;
import hudson.tasks.test.AbstractTestResultAction;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;
import java.util.Set;
import jenkins.model.Jenkins;
import jenkins.scm.RunWithSCM;
import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import org.jenkinsci.plugins.plaincredentials.StringCredentials;
import org.kohsuke.stapler.StaplerRequest2;
import org.kohsuke.stapler.StaplerResponse2;

@Extension
public class ChatbotApiAction implements RootAction {

    private static final String BASE_URL = "chatbot-api";

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

    private StringCredentials getCredentials(ChatbotGlobalConfig pluginConfig) {
        String storedSecretId = pluginConfig.getJwtSecretId();

        if (storedSecretId == null) return null;

        return CredentialsMatchers.firstOrNull(
                CredentialsProvider.lookupCredentialsInItemGroup(
                        StringCredentials.class,
                        Jenkins.get(),
                        ACL.SYSTEM2,
                        URIRequirementBuilder.create().build()),
                CredentialsMatchers.withId(storedSecretId));
    }

    private String generateToken(String secret, long ttl) {
        Algorithm signingAlgorithm = Algorithm.HMAC256(secret);

        return JWT.create()
                .withIssuer("jenkins-chatbot-proxy")
                .withClaim("sub", Jenkins.getAuthentication2().getName())
                .withIssuedAt(new Date())
                .withExpiresAt(new Date(System.currentTimeMillis() + ttl))
                .sign(signingAlgorithm);
    }

    public String getUIPath(StaplerRequest2 request) throws Exception {
        String currentUiPath = "/";

        String refererUrl = request.getHeader("Referer");
        if (refererUrl != null && !refererUrl.isEmpty()) {
            java.net.URI uri = new java.net.URI(refererUrl);
            currentUiPath = uri.getPath();

            String jenkinsRootUrl = jenkins.model.Jenkins.get().getRootUrl();
            if (jenkinsRootUrl != null) {
                String rootPath = new java.net.URI(jenkinsRootUrl).getPath();
                if (rootPath != null && currentUiPath.startsWith(rootPath)) {
                    currentUiPath = currentUiPath.substring(rootPath.length());
                }
            }
        }

        return currentUiPath.startsWith("/") ? currentUiPath : "/" + currentUiPath;
    }

    /**
     * Generates a cascading context payload using Jenkins built-in JSONObject map structure.
     */
    private JSONObject gatherCurrentContext(StaplerRequest2 request) {
        JSONObject rootNode = new JSONObject();

        GlobalAiDecorator decorator = PageDecorator.all().get(GlobalAiDecorator.class);

        String uiPath = null;

        try {
            uiPath = getUIPath(request);
        } catch (Exception e) {
            rootNode.put("contextParsingError", "Failed to parse referer: " + e.getMessage());
        }

        String screenName = (decorator != null) ? decorator.getScreenNameFromPath(uiPath) : "Unknown";
        rootNode.put("currentScreen", screenName);

        addDashboardContext(rootNode);

        String refererUrl = request.getHeader("Referer");
        if (refererUrl != null && !refererUrl.isEmpty()) {
            try {
                if (uiPath != null && uiPath.contains("/job/")) {
                    String[] result = (decorator != null) ? decorator.getJobNameAndBuildNumber(uiPath) : null;
                    String jobName = null;
                    String buildNumber = null;

                    if (result != null) {
                        jobName = result[0];
                        buildNumber = result[1];
                    }

                    if (jobName != null) {
                        Item jenkinsItem = Jenkins.get().getItemByFullName(jobName);
                        if (jenkinsItem instanceof Job) {
                            Job<?, ?> targetJob = (Job<?, ?>) jenkinsItem;

                            addJobContext(rootNode, targetJob);

                            if (buildNumber != null) {
                                Run<?, ?> targetRun = targetJob.getBuildByNumber(Integer.parseInt(buildNumber));
                                if (targetRun != null) {
                                    addBuildContext(rootNode, targetRun);
                                }
                            }
                        }
                    }
                }
            } catch (Exception e) {
                rootNode.put("contextParsingError", e.getMessage());
            }
        }

        return rootNode;
    }

    /**
     * Level 1: Appends core system data, infrastructure stats, and Master Node hardware info.
     */
    private void addDashboardContext(JSONObject rootNode) {
        Jenkins jenkins = Jenkins.get();
        hudson.util.VersionNumber version = Jenkins.getVersion();

        if (version != null) {
            rootNode.put("jenkinsVersion", version.toString());
        }

        // 1. Core Jenkins info
        String rootUrl = jenkins.getRootUrl();
        if (rootUrl != null) {
            rootNode.put("rootUrl", rootUrl);
        }

        String systemMessage = jenkins.getSystemMessage();
        if (systemMessage != null && !systemMessage.isEmpty()) {
            rootNode.put("systemMessage", systemMessage);
        }

        // 2. Active Plugins
        JSONObject pluginsObject = new JSONObject();
        for (hudson.PluginWrapper plugin : jenkins.getPluginManager().getPlugins()) {
            if (plugin.isActive()) {
                pluginsObject.put(plugin.getShortName(), plugin.getVersion());
            }
        }
        rootNode.put("activePlugins", pluginsObject);

        // 3. Master Node (Controller) & System Info
        hudson.model.Computer builtInComputer = jenkins.toComputer();
        if (builtInComputer != null) {
            JSONObject masterNode = new JSONObject();
            masterNode.put("executors", builtInComputer.getNumExecutors());
            masterNode.put("isOnline", builtInComputer.isOnline());

            // JVM and OS Information
            JSONObject systemInfo = new JSONObject();
            systemInfo.put("osName", System.getProperty("os.name"));
            systemInfo.put("osArch", System.getProperty("os.arch"));
            systemInfo.put("osVersion", System.getProperty("os.version"));
            systemInfo.put("javaVersion", System.getProperty("java.version"));

            // Hardware and Memory Stats (Converted to Megabytes for readability)
            Runtime runtime = Runtime.getRuntime();
            systemInfo.put("availableProcessors", runtime.availableProcessors());
            systemInfo.put("freeMemoryMB", runtime.freeMemory() / (1024 * 1024));
            systemInfo.put("totalMemoryMB", runtime.totalMemory() / (1024 * 1024));
            systemInfo.put("maxMemoryMB", runtime.maxMemory() / (1024 * 1024));

            masterNode.put("systemInfo", systemInfo);
            rootNode.put("masterNode", masterNode);
        }

        // 4. Infrastructure Overview (Agent count)
        JSONObject agentStats = new JSONObject();
        int onlineAgents = 0;
        int offlineAgents = 0;

        for (hudson.model.Node node : jenkins.getNodes()) {
            hudson.model.Computer computer = node.toComputer();
            if (computer != null) {
                if (computer.isOnline()) {
                    onlineAgents++;
                } else {
                    offlineAgents++;
                }
            }
        }
        agentStats.put("onlineAgents", onlineAgents);
        agentStats.put("offlineAgents", offlineAgents);
        rootNode.put("agentStats", agentStats);
        System.out.println(rootNode);
    }

    /**
     * Level 2: Appends Job details and configuration fields.
     */
    private void addJobContext(JSONObject rootNode, Job<?, ?> job) throws Exception {
        JSONObject jobDetails = new JSONObject();
        jobDetails.put("fullName", job.getFullName());
        jobDetails.put("jobType", job.getClass().getSimpleName());

        // Basic metadata
        jobDetails.put("url", job.getAbsoluteUrl());
        jobDetails.put("isBuildable", job.isBuildable());
        jobDetails.put("inQueue", job.isInQueue());

        // Health score (0-100, representing the "weather" icon in Jenkins)
        if (job.getBuildHealth() != null) {
            jobDetails.put("healthScore", job.getBuildHealth().getScore());
        }

        // Job description
        String description = job.getDescription();
        if (description != null && !description.isEmpty()) {
            jobDetails.put("description", limitStringSize(description, 1000, false));
        }

        String configXml = job.getConfigFile().asString();
        jobDetails.put("configXml", limitStringSize(configXml, 5000, false));

        // Pipeline vs Classic specific info
        if (job.getClass().getSimpleName().contains("WorkflowJob")) {
            jobDetails.put("isPipeline", true);
        } else {
            jobDetails.put("isPipeline", false);

            // For Classic projects, extract trigger dependencies
            if (job instanceof AbstractProject) {
                AbstractProject<?, ?> abstractProject = (AbstractProject<?, ?>) job;

                JSONArray upstream = new JSONArray();
                for (AbstractProject<?, ?> up : abstractProject.getUpstreamProjects()) {
                    upstream.add(up.getFullName());
                }
                jobDetails.put("upstreamProjects", upstream);

                JSONArray downstream = new JSONArray();
                for (AbstractProject<?, ?> down : abstractProject.getDownstreamProjects()) {
                    downstream.add(down.getFullName());
                }
                jobDetails.put("downstreamProjects", downstream);
            }
        }

        rootNode.put("jobDetails", jobDetails);
        System.out.println(jobDetails);
    }

    /**
     * Level 3: Appends specific execution logs, metrics, and metadata.
     */
    private void addBuildContext(JSONObject rootNode, Run<?, ?> run) throws Exception {
        JSONObject buildDetails = new JSONObject();
        buildDetails.put("number", run.getNumber());

        hudson.model.Result currentResult = run.getResult();
        buildDetails.put("result", currentResult != null ? currentResult.toString() : "IN_PROGRESS");

        buildDetails.put("duration", run.getDuration());
        buildDetails.put("timestamp", run.getTimestamp().getTimeInMillis());

        // 1. Build Causes (Why did it start?)
        CauseAction causeAction = run.getAction(CauseAction.class);
        if (causeAction != null) {
            JSONArray causes = new JSONArray();
            for (Cause cause : causeAction.getCauses()) {
                causes.add(cause.getShortDescription());
            }
            buildDetails.put("causes", causes);
        }

        // 2. Build Parameters (Were wrong parameters provided?)
        ParametersAction paramsAction = run.getAction(ParametersAction.class);
        if (paramsAction != null) {
            JSONObject params = new JSONObject();
            for (ParameterValue p : paramsAction.getParameters()) {
                // parameter values can be strings, booleans, etc.
                params.put(p.getName(), p.getValue());
            }
            buildDetails.put("parameters", params);
        }

        // 3. Test Results (Did it fail because of code tests?)
        AbstractTestResultAction<?> testAction = run.getAction(AbstractTestResultAction.class);

        if (testAction != null) {
            JSONObject tests = new JSONObject();
            tests.put("total", testAction.getTotalCount());
            tests.put("failed", testAction.getFailCount());
            tests.put("skipped", testAction.getSkipCount());
            buildDetails.put("testResults", tests);
        }

        // 4. Execution Node (For classic projects, identifies where it ran)
        if (run instanceof hudson.model.AbstractBuild) {
            Node builtOn = ((hudson.model.AbstractBuild<?, ?>) run).getBuiltOn();
            if (builtOn != null) {
                buildDetails.put("builtOnNode", builtOn.getNodeName());
            }
        }

        List<String> logLines = run.getLog(1000);
        String combinedLogs = String.join("\n", logLines);
        buildDetails.put("consoleLogTail", combinedLogs);

        if (run instanceof RunWithSCM<?, ?>) {
            RunWithSCM<?, ?> runWithScm = (RunWithSCM<?, ?>) run;
            List<ChangeLogSet<? extends Entry>> changeSets = runWithScm.getChangeSets();

            JSONArray changes = new JSONArray();
            int commitCount = 0;

            for (ChangeLogSet<? extends Entry> set : changeSets) {
                for (Entry entry : set) {
                    if (commitCount >= 50) {
                        break;
                    }

                    JSONObject commit = new JSONObject();
                    commit.put("commitId", entry.getCommitId());
                    commit.put("author", entry.getAuthor().getFullName());

                    // Truncate the message just in case it's an extremely long commit description
                    commit.put("message", limitStringSize(entry.getMsg(), 500, false));

                    changes.add(commit);
                    commitCount++;
                }
            }

            if (!changes.isEmpty()) {
                buildDetails.put("changes", changes);
            }
        }

        Run<?, ?> previousRun = run.getPreviousBuild();
        if (previousRun != null) {
            JSONObject prevBuildDetails = new JSONObject();
            prevBuildDetails.put("number", previousRun.getNumber());

            hudson.model.Result prevResult = previousRun.getResult();
            prevBuildDetails.put("result", prevResult != null ? prevResult.toString() : "UNKNOWN");

            buildDetails.put("previousBuild", prevBuildDetails);
        }

        rootNode.put("buildDetails", buildDetails);
        System.out.println(buildDetails);
    }

    /**
     * Helper utility to safely truncate long strings to preserve network efficiency.
     */
    private String limitStringSize(String rawValue, int maxLength, boolean fromBottom) {

        if (rawValue == null) {
            return "";
        }
        if (rawValue.length() > maxLength) {
            if (fromBottom) {
                return "... [CONTENT TRUNCATED]" + rawValue.substring(rawValue.length() - maxLength);
            } else {
                return rawValue.substring(0, maxLength) + "... [CONTENT TRUNCATED]";
            }
        }
        return rawValue;
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
            response.sendError(500, "Backend URL is missing in Jenkins Global Configuration.");
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

        Set<String> stateChangingMethods = Set.of("POST", "PUT", "DELETE");
        String currentMethod = request.getMethod().toUpperCase();

        if (stateChangingMethods.contains(currentMethod)) {
            proxyConnection.setDoOutput(true);

            // Path that requires the context injection
            String contextInjectionPath = "/context/";

            String normalizedPath = dynamicPath.startsWith("/") ? dynamicPath : "/" + dynamicPath;

            if (normalizedPath.startsWith(contextInjectionPath)) {

                try (InputStream clientRequestStream = request.getInputStream();
                        OutputStream downstreamStream = proxyConnection.getOutputStream()) {

                    String requestBody =
                            new String(clientRequestStream.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);

                    try {
                        // Parse the payload into a JSON object
                        JSONObject payload =
                                requestBody.isEmpty() ? new JSONObject() : JSONObject.fromObject(requestBody);

                        // Generate the Jenkins context and parse it as a JSON object
                        JSONObject contextJson = gatherCurrentContext(request);

                        // Inject the context into the main payload under a specific key
                        payload.put("jenkinsContext", contextJson);

                        // Convert back to string and write to the downstream backend
                        byte[] modifiedBodyBytes = payload.toString().getBytes(StandardCharsets.UTF_8);
                        downstreamStream.write(modifiedBodyBytes);

                    } catch (Exception e) {
                        byte[] originalBytes = requestBody.getBytes(StandardCharsets.UTF_8);
                        downstreamStream.write(originalBytes);
                    }
                    downstreamStream.flush();
                }

            } else {
                try (InputStream clientRequestStream = request.getInputStream();
                        OutputStream downstreamStream = proxyConnection.getOutputStream()) {
                    clientRequestStream.transferTo(downstreamStream);
                }
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
        boolean isServerSentEvents = downstreamContentType != null
                && downstreamContentType.toLowerCase().contains("text/event-stream");

        if (isServerSentEvents) {
            // Prevent the browser and intermediate proxies from buffering the stream
            response.setHeader("Cache-Control", "no-cache");
            response.setHeader("Connection", "keep-alive");
        }

        // Return the payload back to the originating client
        try (InputStream downstreamResponseStream = (downstreamResponseCode >= 200 && downstreamResponseCode < 300)
                        ? proxyConnection.getInputStream()
                        : proxyConnection.getErrorStream();
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
