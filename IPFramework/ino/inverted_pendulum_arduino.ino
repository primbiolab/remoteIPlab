// Encoder pins
const int motorEncoderPinA = 3;
const int motorEncoderPinB = 2;
const int angleEncoderPinA = 18;
const int angleEncoderPinB = 19;

// Motor control pins
const int motorPWMPin = 10;
const int motorIN1 = 6;
const int motorIN2 = 7;
const int motorEnablePin = 5;

// Encoder positions
volatile long motorPosition = 0;
volatile long angleStepCount = 0;
volatile byte motorLastEncoded = 0;
volatile byte angleLastEncoded = 0;

// Other variables
unsigned long lastTime = 0;
long lastMotorPosition = 0;
long lastAngleStepCount = 0;
float motorSpeed = 0;
float angularSpeed = 0;
bool usePositionControl = true;
long desiredPosition = 0;
const int fixedVoltage = 100;
const int positionTolerance = 100;
int voltageOutput = 0;

// Angle calculation constants
const float encoderStepsPerRevolution = 2400; // Adjusted for 4x PPR (400 * 4)
const float gearRatio = 1.0;

// Variables for smoothing
const int bufferSize = 10;
unsigned long timeBuffer[bufferSize];
long motorPositionBuffer[bufferSize];
long angleStepCountBuffer[bufferSize];
int bufferIndex = 0;

// ===== Calibration variables =====
long railLeftLimit = 0;    // left rail limit in encoder pulses
long railRightLimit = 0;   // right rail limit in encoder pulses
long railCenter = 0;       // center position in encoder pulses
const long FALLBACK_LIMIT = 5000;  // fallback hard limit if no calibration
const bool INVERT_MOTOR_DIRECTION = true;  // true if encoder counts opposite to motor direction

void setup() {
  Serial.begin(115200);
  
  pinMode(motorEncoderPinA, INPUT_PULLUP);
  pinMode(motorEncoderPinB, INPUT_PULLUP);
  pinMode(angleEncoderPinA, INPUT_PULLUP);
  pinMode(angleEncoderPinB, INPUT_PULLUP);
  
  pinMode(motorPWMPin, OUTPUT);
  pinMode(motorIN1, OUTPUT);
  pinMode(motorIN2, OUTPUT);
  pinMode(motorEnablePin, OUTPUT);

  attachInterrupt(digitalPinToInterrupt(motorEncoderPinA), readMotorEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(motorEncoderPinB), readMotorEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(angleEncoderPinA), readAngleEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(angleEncoderPinB), readAngleEncoder, CHANGE);

  digitalWrite(motorEnablePin, LOW); // Initially disable the motor
  
  // Initialize buffers
  unsigned long currentTime = micros();
  for (int j = 0; j < bufferSize; j++) {
    timeBuffer[j] = currentTime;
    motorPositionBuffer[j] = motorPosition;
    angleStepCountBuffer[j] = angleStepCount;
  }
  
  Serial.println("Inverted Pendulum System Ready");
}

void loop() {
  unsigned long currentTime = micros();

  // Update buffers
  bufferIndex = (bufferIndex + 1) % bufferSize;
  timeBuffer[bufferIndex] = currentTime;
  motorPositionBuffer[bufferIndex] = motorPosition;
  angleStepCountBuffer[bufferIndex] = angleStepCount;
  
  // Calculate smoothed speeds
  int oldestIndex = (bufferIndex + 1) % bufferSize;
  float deltaTime = (currentTime - timeBuffer[oldestIndex]) / 1000000.0;
  motorSpeed = (motorPosition - motorPositionBuffer[oldestIndex]) / deltaTime;
  angularSpeed = (angleStepCount - angleStepCountBuffer[oldestIndex]) * (360.0 / encoderStepsPerRevolution) / gearRatio / deltaTime;

  // Calculate angle from vertical (0 degrees is vertical, positive is clockwise)
  float angle = calculateAngle(angleStepCount);

  // Handle serial input
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    if (input.length() == 0) return;
    char cmd = input.charAt(0);

    if (cmd == 'R') {
      sendData(motorPosition, angle, motorSpeed, angularSpeed);
    } else if (cmd == 'Z') {
      // Reset ALL: encoder, limits and center
      motorPosition = 0;
      lastMotorPosition = 0;
      railLeftLimit = 0;
      railRightLimit = 0;
      railCenter = 0;
      usePositionControl = false;
      voltageOutput = 0;
      for (int j = 0; j < bufferSize; j++) {
        motorPositionBuffer[j] = 0;
      }
      Serial.println("Z_OK");
    } else if (cmd == 'C') {
      // Calibration mode: read-only, motor disabled
      digitalWrite(motorEnablePin, LOW);
      digitalWrite(motorIN1, LOW);
      digitalWrite(motorIN2, LOW);
      analogWrite(motorPWMPin, 0);
      sendData(motorPosition, angle, motorSpeed, angularSpeed);
      return;
    } else if (cmd == 'E') {
      // Set left rail limit to current position (motor disabled)
      digitalWrite(motorEnablePin, LOW);
      digitalWrite(motorIN1, LOW);
      digitalWrite(motorIN2, LOW);
      analogWrite(motorPWMPin, 0);
      usePositionControl = false;
      voltageOutput = 0;
      railLeftLimit = motorPosition;
      Serial.print("E_OK,");
      Serial.println(railLeftLimit);
      return; // Skip motor control — user must move cart freely
    } else if (cmd == 'D') {
      // Set right rail limit to current position (motor disabled)
      digitalWrite(motorEnablePin, LOW);
      digitalWrite(motorIN1, LOW);
      digitalWrite(motorIN2, LOW);
      analogWrite(motorPWMPin, 0);
      usePositionControl = false;
      voltageOutput = 0;
      railRightLimit = motorPosition;
      Serial.print("D_OK,");
      Serial.println(railRightLimit);
      return; // Skip motor control — user must move cart freely
    } else if (cmd == 'O') {
      // Compute center from left and right limits
      digitalWrite(motorEnablePin, LOW);
      digitalWrite(motorIN1, LOW);
      digitalWrite(motorIN2, LOW);
      analogWrite(motorPWMPin, 0);
      railCenter = (railLeftLimit + railRightLimit) / 2;
      Serial.print("O_OK,");
      Serial.print(railCenter);
      Serial.print(",");
      Serial.print(railLeftLimit);
      Serial.print(",");
      Serial.println(railRightLimit);
      return; // Skip motor control
    } else if (cmd == 'H') {
      // Move to center (home)
      usePositionControl = true;
      desiredPosition = railCenter;
      Serial.println("H_OK");
    } else if (cmd == 'A') {
      // Apply calibration: center pasa a ser 0 y los extremos quedan simétricos
      long offset = railCenter;
      motorPosition -= offset;
      lastMotorPosition = motorPosition;
      railLeftLimit -= offset;
      railRightLimit -= offset;
      railCenter = 0;
      desiredPosition = 0;
      usePositionControl = false;
      voltageOutput = 0;
      for (int j = 0; j < bufferSize; j++) {
        motorPositionBuffer[j] = motorPosition;
      }
      Serial.println("A_OK");
    } else {
      parseCommand(input);
    }
  }

  // Motor control
  int output;
  if (usePositionControl) {
    long positionError = desiredPosition - motorPosition;
    if (abs(positionError) <= positionTolerance) {
      output = 0;
    } else {
      long activeLimit = FALLBACK_LIMIT;
      if (railLeftLimit != 0 && railRightLimit != 0) {
        activeLimit = max(abs(railLeftLimit), abs(railRightLimit));
      }
      int pwm = map(abs(positionError), positionTolerance, activeLimit, 60, 255);
      pwm = constrain(pwm, 60, 255);
      if (positionError > 0) {
        output = pwm;
      } else {
        output = -pwm;
      }
    }
    if (INVERT_MOTOR_DIRECTION) {
      output = -output;
    }
  } else {
    output = voltageOutput;
  }

  // Soft limits con recuperación al centro (solo tras fijar AMBOS extremos)
  if (railLeftLimit != 0 && railRightLimit != 0) {
    if (motorPosition < railLeftLimit) {
      output = INVERT_MOTOR_DIRECTION ? -170 : 170;
    } else if (motorPosition > railRightLimit) {
      output = INVERT_MOTOR_DIRECTION ? 170 : -170;
    }
  }

  setMotor(output);
  delay(1);
}

void readMotorEncoder() {
  byte MSB = digitalRead(motorEncoderPinA);
  byte LSB = digitalRead(motorEncoderPinB);
  byte encoded = (MSB << 1) | LSB;
  byte sum = (motorLastEncoded << 2) | encoded;

  if (sum == 0b1101 || sum == 0b0100 || sum == 0b0010 || sum == 0b1011) motorPosition++;
  if (sum == 0b1110 || sum == 0b0111 || sum == 0b0001 || sum == 0b1000) motorPosition--;

  motorLastEncoded = encoded;
}

void readAngleEncoder() {
  byte MSB = digitalRead(angleEncoderPinA);
  byte LSB = digitalRead(angleEncoderPinB);
  byte encoded = (MSB << 1) | LSB;
  byte sum = (angleLastEncoded << 2) | encoded;

  if (sum == 0b1101 || sum == 0b0100 || sum == 0b0010 || sum == 0b1011) angleStepCount++;
  if (sum == 0b1110 || sum == 0b0111 || sum == 0b0001 || sum == 0b1000) angleStepCount--;

  angleLastEncoded = encoded;
}

float calculateAngle(long stepCount) {
  float rawAngle = (stepCount / encoderStepsPerRevolution) * 360.0 / gearRatio;
  rawAngle = fmod(rawAngle, 360.0);
  if (rawAngle < 0) rawAngle += 360.0;
  
  float adjustedAngle = rawAngle + 180.0;
  if (adjustedAngle >= 360.0) adjustedAngle -= 360.0;
  
  if (adjustedAngle > 180.0) adjustedAngle -= 360.0;
  
  return adjustedAngle;
}

void setMotor(int output) {
  if (output != 0) {
    digitalWrite(motorEnablePin, HIGH);
    if (output > 0) {
      digitalWrite(motorIN1, HIGH);
      digitalWrite(motorIN2, LOW);
    } else {
      digitalWrite(motorIN1, LOW);
      digitalWrite(motorIN2, HIGH);
    }
    analogWrite(motorPWMPin, abs(output));
  } else {
    digitalWrite(motorEnablePin, LOW);
    digitalWrite(motorIN1, LOW);
    digitalWrite(motorIN2, LOW);
    analogWrite(motorPWMPin, 0);
  }
}

void sendData(long motorPos, float angle, float motorSpd, float angularSpd) {
  Serial.print(motorPos);
  Serial.print(",");
  Serial.print(angle);
  Serial.print(",");
  Serial.print(motorSpd);
  Serial.print(",");
  Serial.println(angularSpd);
}

void parseCommand(String command) {
  usePositionControl = command.charAt(0) - '0';
  String valueStr = command.substring(1);
  float value = valueStr.toFloat();
  
  if (usePositionControl) {
    desiredPosition = value;
  } else {
    voltageOutput = map(value, -12, 12, -255, 255);
  }
}
