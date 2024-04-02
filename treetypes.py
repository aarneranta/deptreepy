from dataclasses import dataclass
from typing import Iterable

from trees import *

@dataclass
class TreeType:
    "the 'type' of a deptree: (POS, DEPREL)* -> (POS, DEPREL) of head and dependents"
    args: list[tuple[str, str]]  # POS, DEPREL
    val: tuple[str, str]

    def __str__(self):
        return ' -> '.join([str(arg) for arg in self.args] + [str(self.val)])


def deptree2treetype(tree: DepTree) -> TreeType:
    val = (tree.root.POS, tree.root.DEPREL)
    args = [(t.root.POS, t.root.DEPREL) for t in tree.subtrees]
    return TreeType(args, val)


def deptree2treetypes(tree: DepTree) -> list[TreeType]:
    typs = [deptree2treetype(tree)]
    for t in tree.subtrees:
        for typ in deptree2treetypes(t):
            typs.append(typ)
    return typs


def treetype_statistics_dict(trees: Iterable[DepTree]) -> dict[str, int]:
    dict = {}
    for tree in trees:
        for typ in deptree2treetypes(tree):
            dict[str(typ)] = dict.get(str(typ), 0) + 1

    return dict



