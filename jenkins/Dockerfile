# Stage 1: Build the plugin (including the React frontend)
FROM maven:3.9-eclipse-temurin-17 AS plugin-builder

WORKDIR /plugin_build

# Copy Maven definitions
COPY pom.xml .

# Copy source code (Java backend and React frontend)
COPY src ./src
COPY frontend ./frontend

# Compile the plugin (this will trigger Vite build automatically)
RUN mvn clean package -DskipTests

# Stage 2: Setup Jenkins middleware
FROM jenkins/jenkins:lts-jdk17

COPY jenkins/plugins.txt /usr/share/jenkins/ref/plugins.txt

RUN jenkins-plugin-cli -f /usr/share/jenkins/ref/plugins.txt

# Disable the initial setup wizard
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

# Install Configuration as Code plugin for environment variables mapping
RUN jenkins-plugin-cli --plugins "configuration-as-code"

# Copy the fully compiled .hpi (Java + React inside)
COPY --from=plugin-builder /plugin_build/target/user-guide-ai-chatbot.hpi /usr/share/jenkins/ref/plugins/user-guide-ai-chatbot.hpi

EXPOSE 8080