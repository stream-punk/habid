import warnings

warnings.filterwarnings("ignore")
from thefuzz import fuzz

warnings.filterwarnings("default")

import click
import toml
import random
import readline
from colorama import init, Fore, Style
from dataclasses import dataclass

ra = Style.RESET_ALL


@dataclass
class State:
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


def ask(state, card):
    print(Fore.CYAN + card["prompt"] + ra)
    answers = set(card["answers"])
    len_answers = len(answers)
    ratio = -1
    while answers:
        if ratio != -1:
            print(Fore.YELLOW + f"best ratio: {ratio:3d}%" + ra)
        open = len_answers - len(answers)
        given = input(
            Fore.BLUE + f"\nanswer {open:2d}/{len_answers:2d} (? help): " + ra
        )
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
            print(Fore.GREEN + "correct!" + ra)
            answers.remove(given)
            state.questions += 1
            continue
        best = ""
        last_ratio = 0
        for answer in answers:
            ratio = max(ratio, fuzz.ratio(given, answer))
            if last_ratio != ratio:
                best = answer
            last_ratio = ratio
        factor = 1.0
        if best and best.lower() == given.lower():
            print(Fore.GREEN + "case mismatch only" + ra)
            factor = 0.1
        if given and best and show_hint:
            if full_hint:
                hint = best
            else:
                factor = 0.5
                half = len(best) // 2
                if random.random() > 0.5:
                    hint = best[half:]
                    hint = f"...{hint}"
                else:
                    hint = best[:half]
                    hint = f"{hint}.."
            print(Fore.YELLOW + f"hint: {hint}" + ra)
        state.mistakes += (1.0 - (ratio / 100)) * factor


def train(training, shuffle=True):
    try:
        state = State()
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
def run(trainings, shuffle, join):
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
        train(training, shuffle)
    else:
        for training in data:
            train(training["card"], shuffle)
