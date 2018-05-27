from steppercontroller import StepperController

STEPPER1_STEP_PIN_GPIO = 12  # board pin number 32
STEPPER2_STEP_PIN_GPIO = 13  # board pin number 33

STEPPER1_DIR_PIN_GPIO = 16  # board pin 36
STEPPER2_DIR_PIN_GPIO = 26  # board pin 37

azimuthStepper = StepperController(
    STEPPER1_STEP_PIN_GPIO,
    STEPPER1_DIR_PIN_GPIO)
elevationStepper = StepperController(
    STEPPER2_STEP_PIN_GPIO,
    STEPPER2_DIR_PIN_GPIO)
azimuthStepper.moveForward(1525.0)
#azimuthStepper.moveBackwards(1525.0)
