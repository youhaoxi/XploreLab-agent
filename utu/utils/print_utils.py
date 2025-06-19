from collections import defaultdict

from colorama import Fore, Style, init

init(autoreset=True)  # Reset color to default (autoreset=True handles this automatically)

COLOR_DICT = defaultdict(lambda: Style.RESET_ALL)
COLOR_DICT.update(
    {
        "gray": Fore.LIGHTBLACK_EX,
        "orange": Fore.LIGHTYELLOW_EX,
        "red": Fore.RED,
        "green": Fore.GREEN,
        "blue": Fore.BLUE,
        "yellow": Fore.YELLOW,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE,
        "bold_blue": Style.BRIGHT + Fore.BLUE,
    }
)


class PrintUtils:
    @staticmethod
    def print_input(prompt_text: str, prompt_color="blue", input_color="bold_blue"):
        """styled user input"""
        user_input = input(COLOR_DICT[prompt_color] + prompt_text + COLOR_DICT[input_color])
        print(Style.RESET_ALL, end="")
        return user_input

    @staticmethod
    def print_info(
        msg: str,
        color: str = "gray",
        add_prefix: bool = False,
        prefix: str = "",
        end: str = "\n",
        flush: bool = True,
    ):
        if add_prefix:
            msg = prefix + " " + msg
        print(COLOR_DICT[color] + msg + Style.RESET_ALL, end=end, flush=flush)

    @staticmethod
    def print_bot(
        msg: str,
        color: str = "orange",
        add_prefix: bool = False,
        prefix: str = "[BOT]",
        end: str = "\n",
        flush: bool = True,
    ):
        PrintUtils.print_info(msg, color=color, add_prefix=add_prefix, prefix=prefix, end=end, flush=flush)

    @staticmethod
    def print_tool(
        msg: str,
        color: str = "green",
        add_prefix: bool = False,
        prefix: str = "[TOOL]",
        end: str = "\n",
        flush: bool = True,
    ):
        PrintUtils.print_info(msg, color=color, add_prefix=add_prefix, prefix=prefix, end=end, flush=flush)

    @staticmethod
    def print_error(
        msg: str,
        color: str = "red",
        add_prefix: bool = False,
        prefix: str = "[ERROR]",
        end: str = "\n",
        flush: bool = True,
    ):
        PrintUtils.print_info(msg, color=color, add_prefix=add_prefix, prefix=prefix, end=end, flush=flush)
