package io.jenkins.plugins.chatbot;

import hudson.Extension;
import hudson.model.PageDecorator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Extension
public class GlobalAiDecorator extends PageDecorator {

    private static final Logger log = LoggerFactory.getLogger(GlobalAiDecorator.class);

    public GlobalAiDecorator() {
        super();
    }
}
