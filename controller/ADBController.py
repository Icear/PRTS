import logging
import os
import re
import signal
import subprocess

from controller.Controller import Controller


def exec_run(command):
    with subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as pipe:
        try:
            stdout, stderr = pipe.communicate(timeout=300)
        except subprocess.TimeoutExpired as timeout_ex:
            os.killpg(pipe.pid, signal.SIGUSR1)
            raise timeout_ex
    return stdout, bytes.decode(stderr)


class ADBController(Controller):
    # adb_path = 'adb'
    adb_path = r'adb.exe'

    def __init__(self):
        self.logger = logging.getLogger('ADBController')

        self.logger.info(f"resetting ADB server...")
        output, error = self.exec([self.adb_path, "kill-server"])
        self.logger.debug(f"kill server, result: {output}, stderr: {error}")
        output, error = self.exec([self.adb_path, "start-server"])
        self.logger.debug(f"start server, result: {output}, stderr {error}")
        output, error = self.exec([self.adb_path, "connect", "127.0.0.1:6414"])
        self.logger.debug(f"connect to device, result: {output}, stderr {error}")

        # output, error = self.exec([self.adb_path, "connect", "127.0.0.1:5555"])
        # self.logger.debug(f"connect to device, result: {output}, stderr {error}")

        # self.adb_prefix = ["-s", "127.0.0.1:62025"]
        # self.adb_prefix = ["-s", "127.0.0.1:7555"]
        # self.adb_prefix = ["-s", "127.0.0.1:5555"]
        self.adb_prefix = ["-s", "127.0.0.1:6414"]  # prefix parameters
        # self.adb_prefix = []
        self.wait_for_device()

    def get_device_screen_picture(self):
        output, error = self.exec([self.adb_path] + self.adb_prefix + ["exec-out", "screencap", "-p"])
        if error != '':
            self.logger.error(f"command get_device_screen_picture error: {error}")
            exit(-1)
        self.logger.debug(f"get screen pic, stderr: {error}")
        return output

    def get_device_resolution(self) -> (int, int):
        self.logger.info('getting device screen resolution...')
        pattern = re.compile(r'.*? (\d*?)x(\d*?)$')
        output, error = self.exec([self.adb_path] + self.adb_prefix + ["shell", "wm", "size"])
        if error != '':
            self.logger.error(f"command get_device_resolution error: {error}")
            exit(-1)
        result = bytes.decode(output).strip()
        self.logger.debug(f"check resolution, result: {result}, stderr: {error}")
        match_result = pattern.match(result)
        self.logger.info(
            f"screen size is {match_result[1]}x{match_result[2]}")
        return match_result[1], match_result[2]

    def wait_for_device(self):
        self.logger.info('waiting for device...')
        output, error = self.exec([self.adb_path] + self.adb_prefix + ["wait-for-device"])
        self.logger.debug(f"waiting for device result: {output}, stderr: {error} ")
        if error != '':
            self.logger.error(f"command wait_for_device error: {error}")
            exit(-1)
        self.logger.info('device connected')

    def click(self, x, y):
        x = round(x, 0)
        y = round(y, 0)
        self.logger.info(f"tap({x}, {y})")
        output, error = self.exec([self.adb_path] + self.adb_prefix + ["shell", "input", "tap", str(x), str(y)])
        if error != '':
            self.logger.error(f"command click error: {error}")
            exit(-1)
        self.logger.debug(f"click result: {output}")

    def exec(self, command):
        try:
            stdout, stderr = exec_run(command=command)
            if stderr is None:
                return stdout, None
        except PermissionError as err:
            self.logger.debug(f"exec {command}, get error {err.__class__}: {err}")
            raise err
        except Exception as ex:
            self.logger.debug(f"exec {command}, get exception {ex.__class__}: {ex}")
            raise ex

        self.logger.debug(f"exec {command}, stdout: {stdout}, stderr: {stderr}")
        return stdout, stderr
