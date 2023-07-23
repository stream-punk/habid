import math
import random
import readline
import warnings
from dataclasses import dataclass
from difflib import SequenceMatcher

import click
import toml
from colorama import Fore, Style, init

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
- add a ! in front of your guess to get a hint
- add a !! in front of your guess to get a full hint
- press ctrl-d to quit
""".strip()
        + ra
    )


def lev_ratio(a, b):
    m = SequenceMatcher(None, a, b)
    return int(round(100 * m.ratio()))


def ask(state, card):
    print()
    print(Fore.CYAN + card["prompt"] + ra)
    answer_list = list(card["answers"])
    answers = dict()
    has_primary = False
    for answer in answer_list:
        answer = answer.strip()
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
        readline.add_history(given)
        given = given.strip()
        show_hint = given.startswith("!")
        full_hint = False
        if show_hint:
            full_hint = given.startswith("!!")
            start = 1
            if full_hint:
                start = 2
            given = given[start:]
        if given == "?":
            help()
            continue
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
        for answer in answers:
            ratio = max(ratio, lev_ratio(given, answer))
            if last_ratio != ratio:
                best = answer
            last_ratio = ratio
        factor = 1.0
        if best.lower() == given.lower():
            print(Fore.GREEN + "case mismatch only" + ra)
            factor = 0.1
        if show_hint:
            if full_hint:
                hint = best
            else:
                factor = 0.5
                len_best = len(best)
                half = len_best // 2
                coin = random.random() > 0.5
                if coin:
                    part = best[half:]
                else:
                    part = best[: half + 1]
                rest = "." * (len_best - len(part))
                if coin:
                    hint = f"{rest}{part}"
                else:
                    hint = f"{part}{rest}"
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
@click.option("--join/--no-join", "-j/-nj", default=True, help="Join all trainings")
@click.option("--one/--no-one", "-o/-no", default=False, help="One answer is enough")
def run(trainings, shuffle, join, one):
    if not trainings:
        raise click.BadParameter("Please set at least one training-file.")
    data = []
    for training in trainings:
        if not training.endswith(".toml"):
            raise click.BadParameter(f"{training} is not a toml-file")
        data.append(toml.load(training))
    init()
    if join:
        training = []
        for data_set in data:
            training.extend(data_set["card"])
        train(training, shuffle, one)
    else:
        for training in data:
            train(training["card"], shuffle, one)
