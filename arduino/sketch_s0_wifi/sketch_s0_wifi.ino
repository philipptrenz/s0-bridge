// Load Wi-Fi library
#include <ESP8266WiFi.h>

// Replace with your network credentials
const char* ssid     = "ENTER_YOUR_NETWORK_SSID";
const char* password = "ENTER_YOUR_WIFI_PASSWORD";

const int NUM_S0 = 3;
const int s0Pins[] = {5, 4, 0};  // NodeMCU pins D1, D2, D3
const int ledPin = 2;           // NodeMCU pin D0

unsigned long pulseCounter[NUM_S0];
unsigned long doBlink = 0;

// Set web server port number to 80
WiFiServer server(80);

// Variable to store the HTTP request
String header;

void handleInterrupt0() {
  pulseCounter[0]++;
  doBlink = millis();
}

void handleInterrupt1() {
  pulseCounter[1]++;
  doBlink = millis();
}

void handleInterrupt2() {
  pulseCounter[2]++;
  doBlink = millis();
}

void setup() {

  // initializing arrays
  for (int i=0; i < NUM_S0; i++) {
    pinMode(s0Pins[i], INPUT);
    pulseCounter[i] = 0;
  }
  attachInterrupt(digitalPinToInterrupt(s0Pins[0]), handleInterrupt0, RISING);
  attachInterrupt(digitalPinToInterrupt(s0Pins[1]), handleInterrupt1, RISING);
  attachInterrupt(digitalPinToInterrupt(s0Pins[2]), handleInterrupt2, RISING);

  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, HIGH); // ESP8266 internal LED is active LOW

  Serial.begin(115200);

  // Connect to Wi-Fi network with SSID and password
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // Print local IP address and start web server
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();
}

void loop(){
  WiFiClient client = server.available();   // Listen for incoming clients

  if (client) {                             // If a new client connects,
    Serial.println("New Client.");          // print a message out in the serial port
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      if (client.available()) {             // if there's bytes to read from the client,
        char c = client.read();             // read a byte, then
        Serial.write(c);                    // print it out the serial monitor
        header += c;
        if (c == '\n') {                    // if the byte is a newline character
          // if the current line is blank, you got two newline characters in a row.
          // that's the end of the client HTTP request, so send a response:
          if (currentLine.length() == 0) {
            // HTTP headers always start with a response code (e.g. HTTP/1.1 200 OK)
            // and a content-type so the client knows what's coming, then a blank line:
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:application/json; charset=utf-8");
            client.println("Connection: close");
            client.println();

            if (header.indexOf("GET /total") >= 0) {
              // send data as json array
              client.print('[');
              for (int i=0; i < NUM_S0; i++) {
                client.print(pulseCounter[i]);
                if (i < NUM_S0-1) client.print(',');
              }
              client.println(']');
            }

            // The HTTP response ends with another blank line
            client.println();
            // Break out of the while loop
            break;
          } else { // if you got a newline, then clear currentLine
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }
      }
    }
    // Clear the header variable
    header = "";
    // Close the connection
    client.stop();
    Serial.println("Client disconnected.");
    Serial.println("");
  }

  // let led blink on every pulse for 125ms
  if ((millis() - doBlink) <= 125) {
    digitalWrite(ledPin, LOW);
  } else {
    digitalWrite(ledPin, HIGH);
  }
}