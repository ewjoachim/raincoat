from colorama import Fore, Style, init as colorama_init


colorama_init()

COLOR_DICT = {
    "neutral": Style.RESET_ALL,
    "match": Fore.YELLOW + Style.BRIGHT,
    "diff@": Fore.CYAN + Style.BRIGHT,
    "diff+": Fore.GREEN,
    "diff-": Fore.RED,
    "message": Fore.WHITE + Style.BRIGHT,
}
SEPARATOR = "=" * 80


class Color(object):
    def __init__(self, color_dict):
        self.color_dict = color_dict

    def get(self, name):
        return self.color_dict.get(name, "")

    def __getitem__(self, name):
        def apply_color(content):
            return self.get(name) + content + self.get("neutral")
        return apply_color


def get_color(color=False):
    color_dict = {}
    if color:
        color_dict = COLOR_DICT

    return Color(color_dict)
