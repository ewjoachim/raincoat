"""
This is a purely internal file that I need distributed for
testing purposes only.

(Raincoat uses itself to test itself, so we need a file in which
we control the changes)
"""

import time


class Umbrella(object):
    def remove_pouch(self):
        pass

    def put_pouch(self):
        pass

    def open(self):
        """
        Only support automatic umbrella for now
        """
        self.button = "pressed"
        self.side = "pointy side up"

    def close(self):
        pass

    def keep_over_me(self):
        pass

    def is_wet(self):
        return True


class RainDetector(object):
    def still_raining(self):
        return True

rain_detector = RainDetector()


def use_umbrella(umbrella):

    # Prepare umbrella
    umbrella.remove_pouch()
    umbrella.open()

    # Use umbrella
    while rain_detector.still_raining():
        umbrella.keep_over_me()

    # Put umbrella away
    umbrella.close()
    while not umbrella.is_wet():
        time.sleep(1)
    umbrella.put_pouch()
