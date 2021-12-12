// Load Wi-Fi library
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoOTA.h>

// Arduino OTA config
const char* hostname = "your-hostname";
const char* otaPassword = "GhQLuPYMeXGTu1D77edkfrVEF5dTT3Y";

// Replace with your network credentials
const char* wifiSSID     = "ENTER_YOUR_NETWORK_SSID";
const char* wifiPassword = "ENTER_YOUR_WIFI_PASSWORD";

const int s0Pin = D1;

unsigned long pulseCounter = 0;
unsigned long doBlink = 0;

ESP8266WebServer webserver(80);

void ICACHE_RAM_ATTR handleInterrupt() {
  pulseCounter++;
  doBlink = millis();
  // Serial.println("Pulse");
}

void handleRoot() {
  webserver.send(200, "text/plain", "I'm online!"); 
}

void handle404() { 
  webserver.send(404, "text/plain", "404: Not found"); 
}

void handleTotal() {
  webserver.send(200, "text/plain", "[" + String(pulseCounter) +  "]"); 
}

void initializeServer() {
  webserver.on("/", handleRoot);
  webserver.on("/total", handleTotal);
  webserver.onNotFound(handle404);
  webserver.begin();
}

void initializeOTA() {
  ArduinoOTA.setPort(3232); // Port defaults to 3232
  ArduinoOTA.setHostname(hostname);
  ArduinoOTA.setPassword(otaPassword);

  // Password can be set with it's md5 value as well
  // ArduinoOTA.setPasswordHash(...);

  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) type = "sketch";
    else type = "filesystem";
    // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
  });

  ArduinoOTA.begin();
}

void setup() {
  // initializing s0 counter
  pinMode(s0Pin, INPUT);
  attachInterrupt(digitalPinToInterrupt(s0Pin), handleInterrupt, RISING);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH); // ESP8266 internal LED is active LOW

  Serial.begin(115200);

  // Connect to Wi-Fi network with SSID and password
  Serial.print("Connecting to ");
  Serial.println(wifiSSID);

  WiFi.begin(wifiSSID, wifiPassword);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");

  Serial.print("WiFi connected, IP address: ");
  Serial.println(WiFi.localIP());
  
  initializeServer();
  initializeOTA();
  
  Serial.println("All set up!");
}

void loop() {
  webserver.handleClient(); 
  ArduinoOTA.handle();

  // let led blink on every pulse for 125ms
  if ((millis() - doBlink) <= 125) digitalWrite(LED_BUILTIN, LOW);
  else digitalWrite(LED_BUILTIN, HIGH);
}