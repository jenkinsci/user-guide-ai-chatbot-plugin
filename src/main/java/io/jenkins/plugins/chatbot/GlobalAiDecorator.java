package io.jenkins.plugins.chatbot;

import hudson.Extension;
import hudson.model.PageDecorator;
import org.kohsuke.stapler.Stapler;
import org.kohsuke.stapler.StaplerRequest2;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Extension
public class GlobalAiDecorator extends PageDecorator {

    private static final Logger log = LoggerFactory.getLogger(GlobalAiDecorator.class);

    public GlobalAiDecorator() {
        super();
    }

    /**
     * Entry point for Jelly rendering. Automatically uses the active request path.
     */
    public String getCurrentScreenName() {
        StaplerRequest2 request = Stapler.getCurrentRequest2();
        if (request == null || request.getPathInfo() == null) {
            return "Unknown Page";
        }
        return getScreenNameFromPath(request.getPathInfo());
    }

    /**
     * Determines the readable name of the page the user is currently viewing.
     */
    public String getScreenNameFromPath(String path) {
        if (path == null || path.isEmpty()) {
            return "Unknown Page";
        }

        try {
            // Map common Jenkins URL patterns to readable page names

            // Dashboard / Home
            if (path.equals("/") || path.endsWith("/jenkins/")) {
                return "Dashboard";
            }

            // Manage Jenkins section
            if (path.contains("/manage/")) {
                if (path.endsWith("/manage/configure")) {
                    return "System Configuration";
                } else if (path.endsWith("/manage/pluginManager/")) {
                    return "Plugin Manager";
                }
                return "Manage Jenkins";
            }

            // Job / Pipeline pages
            if (path.contains("/job/")) {
                String[] result = getJobNameAndBuildNumber(path);

                String targetJobName = result[0];
                String buildNumber = result[1];

                if (targetJobName != null) {
                    if (path.endsWith("/configure")) {
                        return "Configuration Job " + targetJobName;
                    } else if (buildNumber != null) {
                        if (path.endsWith("/console")) {
                            return "Console Job " + targetJobName;
                        }
                        return "Build Job " + targetJobName;
                    }
                    return "Job " + targetJobName;
                }
            }

            // Nodes / Executors
            if (path.contains("/computer/")) {
                return "Manage Nodes and Clouds";
            }

            return "Generic Page";

        } catch (Exception e) {
            return "Unknown Page";
        }
    }

    public String[] getJobNameAndBuildNumber(String path) {
        String[] result = new String[2];
        String[] urlSegments = path.split("/");

        for (int i = 0; i < urlSegments.length; i++) {
            if ("job".equals(urlSegments[i]) && i + 1 < urlSegments.length) {
                result[0] = urlSegments[i + 1];
            }
            // Check if the URL contains a build number (digits)
            if (result[0] != null && i + 2 < urlSegments.length && urlSegments[i + 2].matches("\\d+")) {
                result[1] = urlSegments[i + 2];
            }
        }

        return result;
    }
}
