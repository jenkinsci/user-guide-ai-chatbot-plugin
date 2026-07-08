package io.jenkins.plugins.chatbot;

import hudson.Extension;
import hudson.model.PageDecorator;
import org.kohsuke.stapler.Stapler;
import org.kohsuke.stapler.StaplerRequest2;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;

@Extension
public class GlobalAiDecorator extends PageDecorator {

    private static final Logger log = LoggerFactory.getLogger(GlobalAiDecorator.class);

    public GlobalAiDecorator() {
        super();
    }

    /**
     * Determines the readable name of the page the user is currently viewing.
     */
    public String getCurrentScreenName() {
        StaplerRequest2 request = Stapler.getCurrentRequest2();
        if (request == null) {
            return "Unknown Page";
        }

        String path = request.getPathInfo();

        if (path == null) {
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
                String[] urlSegments = path.split("/");
                String targetJobName = null;
                String buildNumber = null;

                for (int i = 0; i < urlSegments.length; i++) {
                    if ("job".equals(urlSegments[i]) && i + 1 < urlSegments.length) {
                        targetJobName = urlSegments[i + 1];
                    }
                    // Check if the URL contains a build number (digits)
                    if (targetJobName != null && i + 2 < urlSegments.length && urlSegments[i + 2].matches("\\d+")) {
                        buildNumber = urlSegments[i + 2];
                    }
                }

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

            return "Jenkins Generic Page (Path: " + path + ")";

        } catch (Exception e) {
            return "Unknown Page";
        }
    }

}
