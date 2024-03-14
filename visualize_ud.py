import sys
from argparse import ArgumentParser, ArgumentTypeError
from itertools import chain, repeat, islice

import drawsvg as draw

from trees import read_wordlines

# measures
SPACE_LEN = 10
DEFAULT_WORD_LEN = 20
CHAR_LEN = 1.8

# stores CoNLL-U sentence info to be visualized (corresponds to Haskell's Dep)
# NOTE: all positions are real positions and not token IDs, hence the -1s
class VisualStanza:
  def __init__(self,stanza):
    ls = stanza.split("\n")

    # parse stanza as list of wordlines, but ignore tokens whose ID is not 
    # an int (floats & ranges)
    wls = [wl for wl in read_wordlines(ls) if wl.ID.isdigit()]

    # dictionary {token position: word token length}
    # the "token length" is based on the longest between POS and FORM
    self.token_lens = {
      i: CHAR_LEN * max(0, len(wl.FORM), len(wl.POS)) 
      for (i,wl) in enumerate(wls)
    }

    # list of word forms paired with their POS tag: [(word form, UPOS tag)]
    self.tokens = [(wl.FORM, wl.POS) for wl in wls] 
      
    # list of dependency relations: [((from,to), label)]
    self.deprels = [
      ((int(wl.ID) - 1, int(wl.HEAD) - 1), wl.DEPREL) for wl in wls
      ]

    # root word position
    self.root = int([wl.ID for wl in wls if wl.HEAD == "0"][0]) - 1
  
  def word_width(self, i): 
    return 100 * (self.token_lens[i] / DEFAULT_WORD_LEN) + SPACE_LEN
  
  def arcs(self):
    return [(min(f,t), max(f,t)) for ((f,t),_) in self.deprels]
  
  # depth of the link from f to t
  def depth(self,f,t):
    # projective arcs "under" (f,t)?
    sub_arcs = [(x,y) for (x,y) in self.arcs() 
                if (f < x and y <= t) or (f == x and y < t)]

    if sub_arcs:
      return 1 + max([0] + [self.depth(x,y) for (x,y) in sub_arcs])
    return 0

  # abs height of the arc between nodes with positions f (from) and t (to)?
  def arc_height(self, f, t):
    return self.depth(min(f,t), max(f,t)) + 1
  
  def to_svg(self):
    words_width = sum([self.word_width(i) for i in range(len(self.tokens))])
    spaces_width = SPACE_LEN * (len(self.tokens) - 1)
    w = words_width + spaces_width
    h = 50 + 20 * max([0] + [self.arc_height(f,t) for (f,t) in self.arcs()])
    print(w,h)

if __name__ == "__main__":
  intxt = sys.stdin.read()
  stanzas = [span for span in intxt.split("\n\n") if span.strip()]
  
  # WIP
  vs = VisualStanza(stanzas[0])
  vs.to_svg() 