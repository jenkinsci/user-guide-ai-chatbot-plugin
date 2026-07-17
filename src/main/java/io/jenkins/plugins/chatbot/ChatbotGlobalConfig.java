package io.jenkins.plugins.chatbot;

import com.cloudbees.plugins.credentials.CredentialsMatchers;
import com.cloudbees.plugins.credentials.common.StandardListBoxModel;
import com.cloudbees.plugins.credentials.domains.URIRequirementBuilder;
import hudson.Extension;
import hudson.security.ACL;
import hudson.util.ListBoxModel;
import jenkins.model.GlobalConfiguration;
import jenkins.model.Jenkins;
import org.jenkinsci.Symbol;
import org.jenkinsci.plugins.plaincredentials.StringCredentials;
import org.kohsuke.stapler.DataBoundSetter;
import org.kohsuke.stapler.QueryParameter;
import org.kohsuke.stapler.interceptor.RequirePOST;

@Extension
@Symbol("chatbotConfig")
public class ChatbotGlobalConfig extends GlobalConfiguration {

    private String backendUrl;

    private String jwtSecretId;

    public ChatbotGlobalConfig() {
        load();
    }

    public String getBackendUrl() {
        return backendUrl;
    }

    @DataBoundSetter
    public void setBackendUrl(String backendUrl) {
        this.backendUrl = backendUrl;
        save();
    }

    public String getJwtSecretId() {
        return jwtSecretId;
    }

    @DataBoundSetter
    public void setJwtSecretId(String jwtSecretId) {
        this.jwtSecretId = jwtSecretId;
        save();
    }

    @RequirePOST()
    public ListBoxModel doFillJwtSecretIdItems(@QueryParameter String jwtSecretId) {
        if (!Jenkins.get().hasPermission(Jenkins.ADMINISTER)) {
            return new StandardListBoxModel().includeCurrentValue(jwtSecretId);
        }

        return new StandardListBoxModel()
                .includeEmptyValue()
                .includeMatchingAs(
                        ACL.SYSTEM2,
                        Jenkins.get(),
                        StringCredentials.class,
                        URIRequirementBuilder.create().build(),
                        CredentialsMatchers.always())
                .includeCurrentValue(jwtSecretId);
    }

    public static ChatbotGlobalConfig get() {
        return GlobalConfiguration.all().get(ChatbotGlobalConfig.class);
    }
}
