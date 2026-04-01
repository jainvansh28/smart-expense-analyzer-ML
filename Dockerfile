FROM eclipse-temurin:17-jdk

RUN apt-get update && apt-get install -y python3 python3-pip maven

WORKDIR /app

COPY . .

RUN pip3 install --break-system-packages -r ml-service/requirements.txt

RUN mvn -f backend/pom.xml clean package -DskipTests

EXPOSE 8080

ENV PORT=8080

CMD sh -c "python3 ml-service/main.py & java -jar backend/target/*.jar"
