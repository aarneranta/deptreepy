# operations that transform dependency structures and can be piped if types match

from trees import *
from typing import Iterable


def str2wordline(line: str) -> WordLine:
    "read a string as a WordLine, fail if not valid"
    return read_wordline(line)


def strs2wordlines(lines: Iterable[str]) -> Iterable[WordLine]:
    "read a sequence of strings as WordLines, ignoring failed ones"
    for line in lines:
        try:
            word = str2wordline(line)
            yield word
        except:
            pass
        

def wordlines2deptree(wordlines: list[WordLine]) -> DepTree:
    "convert a list of wordlines into a deptree"
    return build_deptree(wordlines)


def deptree2wordlines(tree: DepTree) -> list[WordLine]:
    "convert a deptree to a list of wordlines"
    return tree.wordlines()


def wordlines2sentence(wordlines: list[WordLine]) -> str:
    "extract a sentence from a list of wordlines, using the FORM fields"
    return ' '.join([word.FORM for word in self.wordlines()])

