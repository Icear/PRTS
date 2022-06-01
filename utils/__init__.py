import logging
import time


def sleep(fake_time):
    logging.debug(f"schedule sleep for {fake_time} seconds")
    logging.debug(f"start sleep: {time.ctime()}")
    # a = 1
    time.sleep(fake_time)
    logging.debug(f"end sleep: {time.ctime()}")
