"""
Umbrella can unfold to keep you DRY in the rain
"""

import time


def some_decorator(*args):
    pass


class Umbrella(object):
    def remove_pouch(self):
        pass

    def put_pouch(self):
        pass

    def open(self):
        """
        Only support automatic umbrella for now
        """
        if self.automatic:
            self.button = "pressed"
        else:
            self.slide_runner()
        self.side = "pointy side up"

    @some_decorator(
        "argument")
    def close(self):
        pass

    def keep_over_me(self):
        pass

    def is_wet(self):
        return True


class RainDetector(object):
    def still_raining(self):
        return False

rain_detector = RainDetector()


def use_umbrella(umbrella, action):

    # Prepare umbrella
    umbrella.remove_pouch()
    umbrella.open()

    # Use umbrella
    while rain_detector.still_raining():
        action(umbrella)

    # Put umbrella away
    umbrella.close()
    while not umbrella.is_wet():
        time.sleep(1)
    umbrella.put_pouch()


@some_decorator(
    "argument")
def some_function():
    pass


@some_decorator
def some_function_2():
    pass


@some_decorator("argument")
@some_decorator("argument")
def some_function_3():
    pass


def some_function_4():
    string = """
bla"""
    return string
