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


def ask(state, card):
    print(Fore.CYAN + card["prompt"] + ra)
    answers = set(card["answers"])
    len_answers = len(answers)
    ratio = -1
    while answers:
        if ratio != -1:
            print(Fore.YELLOW + f"best ratio: {ratio:3d}%" + ra)
        open = len_answers - len(answers)
        given = input(Fore.BLUE + f"answer: {open:2d}/{len_answers:2d}: " + ra)
        readline.add_history(given)
        ratio = -1
        if given in answers:
            print(Fore.GREEN + "correct!" + ra)
            answers.remove(given)
            state.questions += 1
            continue
        for answer in answers:
            ratio = max(ratio, fuzz.ratio(given, answer))
        state.mistakes += 1.0 - (ratio / 100)


def train(training, shuffle=True):
    state = State()
    if shuffle:
        print(shuffle)
        random.shuffle(training)
    for card in training:
        ask(state, card)
    average = state.mistakes / state.questions
    print(
        Fore.YELLOW + f"You answered {state.questions} questions "
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
