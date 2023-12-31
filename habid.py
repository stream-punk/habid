import random
import readline
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache

import click
import toml
from colorama import Fore, Style, init

try:
    import gnureadline as readline
except ImportError:
    import readline

ra = Style.RESET_ALL


@dataclass
class State:
    one: bool = False
    mistakes: float = 0
    questions: int = 0


def help():
    print(
        Fore.YELLOW
        + """
- add a ! in front of your guess to get a small hint
- add a !! in front of your guess to get a big hint
- add a !!! in front of your guess to get a full hint
- press ctrl-d to quit
""".strip()
        + ra
    )


@lru_cache(maxsize=None)
def lev_ratio(a, b):
    m = SequenceMatcher(None, a, b)
    return int(round(100 * m.ratio()))


def normalize(input, normalization="NFC"):
    return unicodedata.normalize(normalization, input)


def ask(state, card):
    print()
    print(Fore.CYAN + card["prompt"] + ra)
    answer_list = list(card["answers"])
    answers = dict()
    has_primary = False
    for answer in answer_list:
        answer = normalize(answer.strip())
        if answer.startswith("|"):
            has_primary = True
            answer = answer[1:].strip()
            answers[answer] = True
        else:
            answers[answer] = False
    len_answers = len(answers)
    one = state.one or len_answers == 1

    ratio = -1
    while answers:
        if ratio != -1:
            print(Fore.YELLOW + f"best ratio: {ratio:3d}%" + ra)
        open = len_answers - len(answers)
        if one:
            prompt = f"\nanswer [{len_answers}] (? help): "
        else:
            prompt = f"\nanswer [{open}/{len_answers}] (? help): "
        given = input(Fore.BLUE + prompt + ra)
        given = normalize(given.strip())
        show_hint = given.startswith("!")
        full_hint = False
        if show_hint:
            big_hint = given.startswith("!!")
            full_hint = given.startswith("!!!")
            start = 1
            if full_hint:
                start = 3
            if big_hint:
                start = 2
            given = given[start:]
        if given == "?":
            help()
            continue
        readline.add_history(given)
        ratio = -1
        if given in answers:
            state.questions += 1
            if one:
                print(Fore.GREEN + "correct!" + ra)
                break
            if has_primary:
                kind = "primary" if answers[given] else "secondary"
                print(Fore.GREEN + f"correct! ({kind})" + ra)
            else:
                print(Fore.GREEN + "correct!" + ra)
            answers.pop(given)
            continue
        best = ""
        last_ratio = -1
        factor = 1.0
        for answer in answers:
            ratio = max(ratio, lev_ratio(given, answer))
            if last_ratio != ratio:
                best = answer
            last_ratio = ratio
            if answer.lower() == given.lower():
                best = answer
                print(Fore.GREEN + "case mismatch only" + ra)
                factor = 0.1
                break
        if show_hint:
            if full_hint:
                hint = best
            else:
                len_best = len(best)
                half = len_best // 2
                if big_hint:
                    part = best[: half + 1]
                    factor = 0.5
                else:
                    part = best[half:]
                    factor = 0.2
                rest = "." * (len_best - len(part))
                if big_hint:
                    hint = f"{part}{rest}"
                else:
                    hint = f"{rest}{part}"
            print(Fore.YELLOW + f"hint: {hint}" + ra)
        state.mistakes += (1.0 - (ratio / 100)) * factor


def train(training, shuffle=True, one=False):
    try:
        state = State(one)
        if shuffle:
            random.shuffle(training)
        for card in training:
            ask(state, card)
    finally:
        if state.questions:
            average = state.mistakes / state.questions
            print(
                Fore.YELLOW + f"\nYou answered {state.questions} questions "
                f"with an average of {average:.2f} mistakes" + ra
            )


@click.command()
@click.argument(
    "trainings",
    nargs=-1,
    type=click.Path(
        exists=True,
        readable=True,
        file_okay=True,
        dir_okay=False,
    ),
)
@click.option(
    "--shuffle/--no-shuffle",
    "-s/-ns",
    default=True,
    help="Shuffle the cards",
)
@click.option("--count", "-c", default=0, type=int, help="Number of questions")
@click.option("--join/--no-join", "-j/-nj", default=True, help="Join all trainings")
@click.option("--one/--no-one", "-o/-no", default=False, help="One answer is enough")
def run(trainings, shuffle, join, one, count):
    if count < 1:
        count = None
    if not trainings:
        raise click.BadParameter("Please set at least one training-file.")
    data = []
    for training in trainings:
        if not training.endswith(".toml"):
            raise click.BadParameter(f"{training} is not a toml-file")
        data.append(toml.load(training))
    init()
    readline.set_auto_history(False)
    print(Fore.RED + "pro-tio: say prompt and answer out loud." + ra)
    if join:
        training = []
        for data_set in data:
            training.extend(data_set["card"])
        training = training[:count]
        train(training, shuffle, one)
    else:
        for training in data:
            training = training["card"][:count]
            train(training, shuffle, one)
