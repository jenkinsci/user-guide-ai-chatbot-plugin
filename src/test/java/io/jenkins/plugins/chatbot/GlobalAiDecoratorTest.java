package io.jenkins.plugins.chatbot;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.NullAndEmptySource;

class GlobalAiDecoratorTest {

    @ParameterizedTest
    @CsvSource({
        "/, Dashboard",
        "/manage/configure, System Configuration",
        "/manage/, Manage Jenkins",
        "/manage/pluginManager/, Plugin Manager",
        "/job/app/, Job app",
        "/job/app/configure, Configuration Job app",
        "/job/app/12/, Build Job app",
        "/job/app/12/console, Console Job app",
        "/computer/agent1/, Manage Nodes and Clouds",
        "/view/all/, Generic Page",
    })
    void screenNameFromKnownPages(String path, String expected) {
        GlobalAiDecorator instance = new GlobalAiDecorator();
        assertEquals(expected, instance.getScreenNameFromPath(path));
    }

    @ParameterizedTest
    @NullAndEmptySource
    void unknownPageForMissingPath(String path) {
        GlobalAiDecorator instance = new GlobalAiDecorator();
        assertEquals("Unknown Page", instance.getScreenNameFromPath(path));
    }

    @Test
    void parsesJobNameAndBuildNumber() {
        GlobalAiDecorator instance = new GlobalAiDecorator();
        assertArrayEquals(new String[] {"app", "10"}, instance.getJobNameAndBuildNumber("/job/app/10/"));
        assertArrayEquals(new String[] {"app", null}, instance.getJobNameAndBuildNumber("/job/app/lastBuild/"));
        assertArrayEquals(new String[] {null, null}, instance.getJobNameAndBuildNumber("/manage/"));
    }
}
