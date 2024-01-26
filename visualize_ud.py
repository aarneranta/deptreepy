import sys
from argparse import ArgumentParser, ArgumentTypeError
from itertools import chain, repeat, islice

from trees import read_wordlines

VSPACE = "\\vspace{4mm}"

def intersperse(delimiter, seq):
  return islice(chain.from_iterable(zip(repeat(delimiter), seq)), 1, None)

# stores CoNLL-U sentence info to be visualized
# NOTE: all positions are real positions and not token IDs, hence the -1s
class Dep:
  def __init__(self,wordlines):
      # dictionary (token position -> word form length)
      self.word_length = {
        i: len(wl.FORM) for (i,wl) in enumerate(wordlines)
      }

      # essential info about each token (word form, UPOS tag)
      self.tokens = [(wl.FORM, wl.POS) for wl in wordlines] 
      
      # dependency relations: ((from,to), label)
      self.deps = [
        ((int(wl.ID) - 1, int(wl.HEAD) - 1), wl.DEPREL) for wl in wordlines
        ]

      # root word positions
      self.root = int([wl.ID for wl in wordlines if wl.HEAD == "0"][0]) - 1


# LaTeX stuff

# convert CoNNL-U sentence into LaTeX figure
def conllu2latex(stanza):
  wls = []
  for wl in read_wordlines(stanza.split("\n")):
    if wl.ID.isdigit(): # ignore all the stupid floating point and range IDs
      wls.append(wl)
  dep = Dep(wls)
  print(dep.word_length, dep.tokens, dep.deps, dep.root)
  # TODO: convert it to a picture (either intermediate rep or LaTeX code directly)
  return "there will be a tree here"

# embed LaTeX figure in a LaTeX document
def embed_in_latex(latex_tree):
  return "\n".join([
    "\\documentclass{article}",
    "\\usepackage[a4paper,margin=0.5in,landscape]{geometry}",
    "\\usepackage[utf8]{inputenc}",
    "\\begin{document}",
    latex_tree,
    "\\end{document}"
  ])

# convert CoNNL-U string into a list of LaTeX figures
def conllus2latex_doc(stanzas):
  latex_trees = [conllu2latex(stanza) for stanza in stanzas]
  return embed_in_latex("\n".join(intersperse(VSPACE, latex_trees)))


# SVG + HTML stuff

# convert CoNNL-U sentence into SVG figure
def conllu2svg(stanza):
  pass

# embed SVG figure in an HTML document
def embed_in_html(svg_tree):
  pass

# convert CoNNL-U string into a list of LaTeX figures
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
    