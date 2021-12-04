/****************************************************************************************************************************
  HelloServer.ino - Dead simple web-server for Ethernet shields
  
  For Ethernet shields using WT32_ETH01 (ESP32 + LAN8720)
  WebServer_WT32_ETH01 is a library for the Ethernet LAN8720 in WT32_ETH01 to run WebServer
  Based on and modified from ESP8266 https://github.com/esp8266/Arduino/releases
  Built by Khoi Hoang https://github.com/khoih-prog/WebServer_WT32_ETH01
  Licensed under MIT license
 *****************************************************************************************************************************/

#define DEBUG_ETHERNET_WEBSERVER_PORT       Serial

// Debug Level from 0 to 4
#define _ETHERNET_WEBSERVER_LOGLEVEL_       3

#include <WebServer_WT32_ETH01.h>
#include <ArduinoOTA.h>


#define HOSTNAME "zaehler"
#define OTA_PASSWORD "GhQLuPYMeXGTu1D77edkfrVEF5dTT3Y"

WebServer server(80);

// Select the IP address according to your local network
IPAddress myIP(192, 168, 178, 8);
IPAddress myGW(192, 168, 178, 1);
IPAddress mySN(255, 255, 255, 0);

// Google DNS Server IP
IPAddress myDNS(192, 168, 178, 1);

void initializeOTA() 
{
  // Port defaults to 3232
  ArduinoOTA.setPort(3232);
  ArduinoOTA.setHostname(HOSTNAME);
  ArduinoOTA.setPassword(OTA_PASSWORD);

  // Password can be set with it's md5 value as well
  // ArduinoOTA.setPasswordHash(...);

  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH)
      type = "sketch";
    else // U_SPIFFS
      type = "filesystem";

    // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
    Serial.println("Start updating " + type);
  });

  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });

  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println("End Failed");
  });

  ArduinoOTA.begin();
}

void handleRoot()
{
  String html = F("Hello from HelloServer running on ");

  html += String(BOARD_NAME); 
 
  server.send(200, F("text/plain"), html);
}

void handlePowerMeter() {
  String data = "";
  String message = "";
  message += "<html><body><h1>Verbrauchswerte</h1><p>";

  Serial.println("Sending: /?!"); // start sequence
  Serial2.write("/?!\r\n");

  /*
  Serial2.write(0x2F);
  Serial2.write(0x3F);
  Serial2.write(0x21);
  Serial2.write(0x0D);
  Serial2.write(0x0A);
  */

  unsigned long t_start = millis();
  bool isInitial = true;

  while(true) {

    char in = Serial2.read();
    
    if (in==0x0A) data = data + "<br>";
    if (in==0x21 || (millis()-t_start) > 8000) break; // end of message is "!" resp. 0x21
    if (in==0xff) continue;

    Serial.print(in, HEX);
    data += String(in);
  }

  Serial.println();

  message += data;
  message += "</p></body></html>";
  server.send(200, "text/html", message);

}

void handleNotFound()
{
  String message = F("File Not Found\n\n");
  
  message += F("URI: ");
  message += server.uri();
  message += F("\nMethod: ");
  message += (server.method() == HTTP_GET) ? F("GET") : F("POST");
  message += F("\nArguments: ");
  message += server.args();
  message += F("\n");
  
  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  
  server.send(404, F("text/plain"), message);
}

void setup(void) {   
  // Serial is used for debugging and monitoring, if not using espota
  Serial.begin(115200);

  // Wait until initialized
  while (!Serial && (millis() < 3000));

  // Serial2 is connected to IR-Schreib-Lesekopf
  // Configuration for power meter Itron ACE3000 Type 260
  // See: https://wiki.volkszaehler.org/hardware/channels/meters/power/edl-ehz/itron_ace3000_type_260 
  Serial2.begin(300, SERIAL_7E1);

  // Wait until initialized
  while (!Serial2);  

  // Initalizing D0 interface on power meter
  //Serial.println("\nInitializing power meter Itron ACE3000 by sending sequence: '/?!'"); // start sequence
  //Serial2.write("/?!\r\n");
  
  Serial.print("\nStarting Server on " + String(ARDUINO_BOARD));
  Serial.println(" with " + String(SHIELD_TYPE));
  Serial.println(WEBSERVER_WT32_ETH01_VERSION);

  // To be called before ETH.begin()
  WT32_ETH01_onEvent();

  //bool begin(uint8_t phy_addr=ETH_PHY_ADDR, int power=ETH_PHY_POWER, int mdc=ETH_PHY_MDC, int mdio=ETH_PHY_MDIO, 
  //           eth_phy_type_t type=ETH_PHY_TYPE, eth_clock_mode_t clk_mode=ETH_CLK_MODE);
  //ETH.begin(ETH_PHY_ADDR, ETH_PHY_POWER, ETH_PHY_MDC, ETH_PHY_MDIO, ETH_PHY_TYPE, ETH_CLK_MODE);
  ETH.begin(ETH_PHY_ADDR, ETH_PHY_POWER);

  // Static IP, leave without this line to get IP via DHCP
  //bool config(IPAddress local_ip, IPAddress gateway, IPAddress subnet, IPAddress dns1 = 0, IPAddress dns2 = 0);
  ETH.config(myIP, myGW, mySN, myDNS);

  WT32_ETH01_waitForConnect();

  server.on(F("/"), handleRoot);

  server.on(F("/pm"), handlePowerMeter);

  server.on(F("/inline"), []() {
    server.send(200, F("text/plain"), F("This works as well"));
  });

  server.onNotFound(handleNotFound);

  server.begin();

  Serial.print(F("HTTP EthernetWebServer is @ IP : "));
  Serial.println(ETH.localIP());

  initializeOTA();
}

void loop(void) {
  server.handleClient();
  ArduinoOTA.handle();
}