/****************************************************************************************************************************
  HelloServer.ino - Dead simple web-server for Ethernet shields
  
  For Ethernet shields using WT32_ETH01 (ESP32 + LAN8720)
  WebServer_WT32_ETH01 is a library for the Ethernet LAN8720 in WT32_ETH01 to run WebServer
  Based on and modified from ESP8266 https://github.com/esp8266/Arduino/releases
  Built by Khoi Hoang https://github.com/khoih-prog/WebServer_WT32_ETH01
  Licensed under MIT license
 *****************************************************************************************************************************/

#define DEBUG_ETHERNET_WEBSERVER_PORT       Serial2

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


String fetchedData = "";
unsigned long lastFetched = millis();
bool initiallyFetched = false;
bool hasFechted = false;
bool isFetchReading = false;
bool isFetchRead = false;


void initializeOTA() {
  // Port defaults to 3232
  ArduinoOTA.setPort(3232);
  ArduinoOTA.setHostname(HOSTNAME);
  ArduinoOTA.setPassword(OTA_PASSWORD);

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

void handlePowerMeterReading() {
  if (!initiallyFetched || (!hasFechted && (millis() - lastFetched) > 30000)) {
    // Fetch every 30 seconds

    Serial.flush();
    Serial.write("/?!\r\n");

    initiallyFetched = true;
    hasFechted = true;
    isFetchRead = false;

    lastFetched = millis();

  } else if (!isFetchRead && (millis() - lastFetched) > 10000) {
    // Read from Serial 10 seconds after fetch

    if (!isFetchReading) {
      fetchedData = "";
      isFetchReading = true;
    } 

    while(Serial.available() > 0) {
      char in = Serial.read();

      // Add <br> at "\n" resp. 0x0A
      //if (in==0x0A && data.length() > 1) data = data + "<br>";

      // end of message is "!" resp. 0x21, fail after 8 seconds
      if ((fetchedData.charAt(fetchedData.length()-1) != 0x3F && in==0x21) || (millis()-lastFetched) > 8000) {
        isFetchRead = true;
        hasFechted = false;
        isFetchReading = false;
      } 

      fetchedData += String(in);
    }
  }
}

float getCounterReading(String counterId, String data) {
  int idx2 = data.indexOf( counterId + "(");
  if (idx2 <= 0) return -1;

  String tmp = data.substring(idx2+6);
  int end = tmp.indexOf("*kWh)");
  String sub = tmp.substring(0, end);

  return sub.toFloat();
}  

void handleRoot() {
  String message ="<html>";

  message += "<head>";
  message += "<title>Stromzähler</title>";
  message += "<meta charset=\"utf-8\">";
  message += "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">";
  message += "<meta http-equiv=\"refresh\" content=\"10; URL=http://" + myIP.toString() + "/\">";
  message += "</head>";

  message += "<body><h1>Stromzähler</h1>";

  String data = fetchedData;

  if (data.length() > 0) {

    float purchase = getCounterReading("1.8.0", data);
    if (purchase > 0)
      message += "<p><b>Bezug:</b> " + String(purchase) + " kWh</p>";


    float feed = getCounterReading("2.8.0", data);
    if (feed > 0)
      message += "<p><b>Einspeisung:</b> " + String(feed) + " kWh</p>";


    data.replace("\n", "<br>");    
    message += "<details><summary><b>Datagramm</b></summary><p style=\"padding-left: 16px;\">" + data + "</p></details>";

  } else {
    message += "<p><b>Noch keine Daten empfangen</b></p>";
  }


  message += "<p>Vor " + String((millis() - lastFetched) / 1000) + " Sekunden aktualisiert</p>";
  
  message += "</body>";

  message += "</html>";
  server.send(200, "text/html", message);
}

void handleNotFound() {
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

  // Serial is connected to IR-Schreib-Lesekopf
  // Configuration for power meter Itron ACE3000 Type 260
  // See: https://wiki.volkszaehler.org/hardware/channels/meters/power/edl-ehz/itron_ace3000_type_260 
  Serial.begin(300, SERIAL_7E1);

  // Wait until initialized
  while (!Serial);

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

  server.on(F("/inline"), []() {
    server.send(200, F("text/plain"), F("This works as well"));
  });

  server.onNotFound(handleNotFound);
  server.begin();

  initializeOTA();
}

void loop(void) {
  handlePowerMeterReading();
  server.handleClient();
  ArduinoOTA.handle();
}