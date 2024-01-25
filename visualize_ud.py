import sys
from argparse import ArgumentParser, ArgumentTypeError
from itertools import chain, izip, repeat, islice

def intersperse(delimiter, seq):
    return islice(chain.from_iterable(izip(repeat(delimiter), seq)), 1, None)

# LaTeX stuff

def conll2latex(stanza):
    pass

def embed_in_latex(latex_tree):
    pass

def conllus2latex_doc(stanzas):
    latex_trees = [conll2latex(stanza) for stanza in stanzas]
    # TODO: maybe use pylatex instead of join and VSPACE here
    return embed_in_latex("\n".join(intersperse(VSPACE, latex_trees)))


# SVG + HTML stuff

def conllu2svg(stanza):
    pass

def embed_in_latex(svg_tree):
    pass

def conllus2svg_doc(stanzas):
    pass

if __name__ == "__main__":
    intxt = sys.stdin.read()
    stanzas = [span for span in intxt.split("\n\n") if span.strip()]

    argparser = ArgumentParser()
    argparser.add_argument("target", help="latex | svg")
    args = argparser.parse_args()
    tgt = args.target
    if tgt == "latex":
        print(conllus2latex_doc(stanzas))
    elif tgt == "svg":
        print(conllus2svg_doc(stanzas))
    else:
        raise ArgumentTypeError("usage: python visualize_ud.py (latex | svg)")
    