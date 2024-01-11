from dataclasses import dataclass
from typing import Iterable
import pgf
import trees

# experimenting with gf-ud relations

PGF_FILE = 'Lang.pgf'            # from some RGL language
ANNOTATION_FILE = 'Lang.labels'  # from gf-rgl/src

@dataclass
class GFNode:
    FUN: str
    CAT: str
    POS: str
    DEPREL: str

    def has_deprel(self):
        self.deprel is None

    def __str__(self):
        return self.FUN + '[' + ', '.join(
            [str(self.CAT), str(self.POS), str(self.DEPREL)]) + ']'


@dataclass
class AbsTree(trees.Tree):
    "abstract syntax trees: a node is a GF node"

    def fun(self):
        return self.root.FUN
    
    def cat(self):
        return self.root.CAT
    
    def deprel(self):
        return self.root.DEPREL

    
def expr2abstree(gf: pgf.PGF, annots: dict,
                 exp: pgf.Expr, dep: str=None, deps: list=None) -> AbsTree:
    fun, xx = exp.unpack()
    cat = str(gr.inferExpr(exp)[1])
    pos = annots.get(cat, [None])[0]
    deps = annots.get(fun, [None for _ in xx])
    args = [expr2abstree(gr, annots, x, d, deps) for x, d in zip(xx, deps)]
    return AbsTree(GFNode(fun, cat, pos, dep), args)


def get_annotations(filename):
    annots = {}
    with open(filename) as file:
        for line in file:
            ws = line.split()
            if ws:
                fun = ws[0]
                deps = []
                for w in ws[1:]:
                    if w.startswith('-'):
                        break
                    deps.append(w)
                annots[fun] = deps
    return annots


def loop(gr, annots, cnc):
    s = input('parse> ')
    pes = cnc.parse(s)
    if pes:
        _, e = pes.__next__()
        print(e)
        print('\n'.join(expr2abstree(gr, annots, e).prettyprint()))
        print(cnc.bracketedLinearize(e)[0])
    loop(gr, annots, cnc)


if __name__ == '__main__':
    gr = pgf.readPGF(PGF_FILE)
    cnc = list(gr.languages.values())[0]
    annots = get_annotations(ANNOTATION_FILE)
    for a in annots.items():
        print(a)
    loop(gr, annots, cnc)


