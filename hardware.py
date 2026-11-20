import os
import threading
from time import sleep


class LockerHardware:
    """두 락커의 RGB LED와 서보를 독립적으로 제어한다."""

    def __init__(self):
        self.enabled = os.getenv("GPIO_ENABLED", "true").lower() == "true"
        self._mutex = threading.Lock()
        self.devices = {}
        self.config = {
            1: {
                "red": int(os.getenv("LOCKER_1_RED_PIN", "17")),
                "green": int(os.getenv("LOCKER_1_GREEN_PIN", "27")),
                "blue": int(os.getenv("LOCKER_1_BLUE_PIN", "22")),
                "servo": int(os.getenv("LOCKER_1_SERVO_PIN", "12")),
                "lock_angle": int(os.getenv("LOCKER_1_LOCK_ANGLE", "90")),
                "unlock_angle": int(os.getenv("LOCKER_1_UNLOCK_ANGLE", "0")),
            },
            2: {
                "red": int(os.getenv("LOCKER_2_RED_PIN", "23")),
                "green": int(os.getenv("LOCKER_2_GREEN_PIN", "24")),
                "blue": int(os.getenv("LOCKER_2_BLUE_PIN", "25")),
                "servo": int(os.getenv("LOCKER_2_SERVO_PIN", "13")),
                "lock_angle": int(os.getenv("LOCKER_2_LOCK_ANGLE", "90")),
                "unlock_angle": int(os.getenv("LOCKER_2_UNLOCK_ANGLE", "0")),
            },
        }

    def _initialize(self, locker_number):
        if locker_number not in self.config:
            raise ValueError(f"지원하지 않는 락커 번호입니다: {locker_number}")
        if locker_number in self.devices or not self.enabled:
            return

        from gpiozero import AngularServo, RGBLED

        common_anode = os.getenv("RGB_COMMON_ANODE", "false").lower() == "true"
        config = self.config[locker_number]
        led = RGBLED(
            red=config["red"],
            green=config["green"],
            blue=config["blue"],
            active_high=not common_anode,
        )
        servo = AngularServo(
            config["servo"],
            min_angle=0,
            max_angle=90,
            min_pulse_width=0.0005,
            max_pulse_width=0.0025,
        )
        self.devices[locker_number] = {"led": led, "servo": servo}

    def _set_angle(self, locker_number, angle):
        servo = self.devices[locker_number]["servo"]
        servo.angle = angle
        sleep(0.7)
        servo.detach()

    def lock(self, locker_number):
        with self._mutex:
            if not self.enabled:
                print(f"[GPIO 테스트 모드] {locker_number}번 잠금: 빨간 LED")
                return
            self._initialize(locker_number)
            config = self.config[locker_number]
            self._set_angle(locker_number, config["lock_angle"])
            self.devices[locker_number]["led"].color = (1, 0, 0)

    def unlock(self, locker_number):
        with self._mutex:
            if not self.enabled:
                print(f"[GPIO 테스트 모드] {locker_number}번 잠금 해제: 초록 LED")
                return
            self._initialize(locker_number)
            config = self.config[locker_number]
            self._set_angle(locker_number, config["unlock_angle"])
            self.devices[locker_number]["led"].color = (0, 1, 0)
