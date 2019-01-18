const int NUM_S0 = 3;
const int s0Pins[] = {2, 3, 4}; 

unsigned long pulseCounter[NUM_S0];
bool isHigh[NUM_S0];
unsigned long doBlink = 0;

void setup() {
  for (int i=0; i < NUM_S0; i++) {
    pinMode(s0Pins[i], INPUT);
    pulseCounter[i] = 0;
    isHigh[i] = false;
  }
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
}

void loop() {
  for (int i=0; i < NUM_S0; i++) {
    bool isPulse = (digitalRead(s0Pins[i]) == HIGH);
    if (isPulse && isPulse != isHigh[i]) {
      pulseCounter[i] += 1;
      doBlink = millis();
    }
    isHigh[i] = isPulse;
  }

  if ((millis() - doBlink) <= 125) {
    digitalWrite(LED_BUILTIN, HIGH);
  } else {
    digitalWrite(LED_BUILTIN, LOW);
  }

  if (Serial.available() > 0) {
    int incoming = Serial.read(); // empty buffer
    Serial.print('[');
    for (int i=0; i < NUM_S0; i++) {
      Serial.print(pulseCounter[i]);
      if (i < NUM_S0-1) Serial.print(',');
    }
    Serial.println(']');
  }

  
}
