from dataclasses import dataclass
from typing import Iterable

from trees import *

@dataclass
class TreeType:
    "the 'type' of a deptree: (POS, DEPREL)[(POS, DEPREL)*] of head and dependents"
    head: tuple[str, str]
    deps: list[tuple[str, str]]  # POS, DEPREL

    
    def __str__(self):
        return str(self.head) + str(self.deps)

    def __hash__(self):
        return self.__str__().__hash__()


def deptree2treetype(tree: DepTree) -> tuple[TreeType, str]:
    head = (tree.root.POS, tree.root.DEPREL)
    deps = [(t.root.POS, t.root.DEPREL) for t in tree.subtrees]
    return (TreeType(head, deps),
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


def head_dep_statistics_dict(trees: Iterable[DepTree]) -> dict[tuple[tuple[str, str], tuple[str, str]], int]:
    dict = {}
    for tree in trees:
        for typ, _ in deptree2treetypes(tree):
            for item in typ.deps:
                dtyp = (typ.head, item)
                if dtyp in dict:
                    dict[dtyp] = dict[dtyp] + 1
                else:
                    dict[dtyp] = 1

    return dict





