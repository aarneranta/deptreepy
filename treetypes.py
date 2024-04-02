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

    def __hash__(self):
        return self.__str__().__hash__()


def deptree2treetype(tree: DepTree) -> tuple[TreeType, str]:
    val = (tree.root.POS, tree.root.DEPREL)
    args = [(t.root.POS, t.root.DEPREL) for t in tree.subtrees]
    return (TreeType(args, val),
            ' '.join([w.FORM for w in sorted(
                    [t.root for t in tree.subtrees] + [tree.root], key = lambda w: w.ID)]))


def deptree2treetypes(tree: DepTree) -> list[tuple[TreeType, str]]:
    typs = [deptree2treetype(tree)]
    for t in tree.subtrees:
        for typ in deptree2treetypes(t):
            typs.append(typ)
    return typs


def treetype_statistics_dict(trees: Iterable[DepTree]) -> dict[TreeType, tuple[int, str]]:
    dict = {}
    for tree in trees:
        for typ, s in deptree2treetypes(tree):
            if typ in dict:
                dict[typ] = (dict[typ][0] + 1, dict[typ][1])
            else:
                dict[typ] = (1, s)

    return dict



