
FROM eclipse-temurin:17-jdk

RUN apt-get update && apt-get install -y python3 python3-pip maven

WORKDIR /app

COPY . .

RUN pip3 install --break-system-packages -r ml-service/requirements.txt

RUN mvn -f backend/pom.xml clean package -DskipTests

EXPOSE 8080

ENV PORT=8080

CMD sh -c "python3 ml-service/main.py & java -jar backend/target/*.jar"
# Multi-stage build for Spring Boot backend
FROM maven:3.9.5-eclipse-temurin-17 AS build

WORKDIR /app
COPY backend/pom.xml .
# Download dependencies first (layer cache)
RUN mvn dependency:go-offline -B

COPY backend/src ./src
RUN mvn clean package -DskipTests -B

# Runtime image
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

# Render sets PORT env var; default to 8080
EXPOSE 8080

ENTRYPOINT ["java", \
  "-Djava.security.egd=file:/dev/./urandom", \
  "-XX:+UseContainerSupport", \
  "-XX:MaxRAMPercentage=75.0", \
  "-jar", "app.jar"]

