import sys
from argparse import ArgumentParser, ArgumentTypeError
from itertools import chain, repeat, islice

from drawsvg import *

from trees import read_wordlines

# default measures
SPACE_LEN = 15
DEFAULT_WORD_LEN = 20
CHAR_LEN = 1.8
NORMAL_TEXT_SIZE = 16
TINY_TEXT_SIZE = 10
SCALE = 5

# stores CoNLL-U sentence info to be visualized (corresponds to Haskell's Dep)
# NOTE: all positions are real positions and not token IDs, hence the -1s
class VisualStanza:
  def __init__(self,stanza):
    lines = stanza.split("\n")

    # parse stanza as list of wordlines, but ignore tokens whose ID is not 
    # an int (floats & ranges)
    wordlines = [wl for wl in read_wordlines(lines) if wl.ID.isdigit()]

    # list of word tokens (dicts with a form and a pos)
    self.tokens = [({"form": wl.FORM, "pos": wl.POS}) for wl in wordlines] 
      
    # list of dependency relations: [((from,to), label)]
    # note: might have to remove root from here to match Haskell program
    self.deprels = [
      ((int(wl.ID) - 1, int(wl.HEAD) - 1), wl.DEPREL) for wl in wordlines
      ]

    # root word position
    self.root = int([wl.ID for wl in wordlines if wl.HEAD == "0"][0]) - 1
  
  def word_length(self, i): # cf. wordLength
    return CHAR_LEN * max(
      0, 
      len(self.tokens[i]["form"]), 
      len(self.tokens[i]["pos"]))
  
  def normalized_word_length(self, i): # cf. rwld
    return self.word_length(i) / DEFAULT_WORD_LEN

  def word_size(self, i): # cf. wsize
    return 100 * self.normalized_word_length(i) + SPACE_LEN
  
  # start x coordinate of i-th word, cf. wpos
  def word_xpos(self, i): 
    return sum([self.word_size(j) for j in range(i)])
  
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
    words_width = sum([self.word_size(i) for i in range(len(self.tokens))])
    spaces_width = SPACE_LEN * (len(self.tokens) - 1)
    w = words_width + spaces_width
    h = 50 + 20 * max([0] + [self.arc_height(f,t) for (f,t) in self.arcs()])
    svg = Drawing(w,h, origin=(0,0)) # might still need to alter w and h
    
    # draw tokens
    for (i,token) in enumerate(self.tokens):
      x = self.word_xpos(i)
      y = h
      svg.append(Text(token["form"], NORMAL_TEXT_SIZE, x=x, y=y))
      svg.append(Text(token["pos"], TINY_TEXT_SIZE, x=x, y=h-15))
    svg.save_html("example.html")


if __name__ == "__main__":
  intxt = sys.stdin.read()
  stanzas = [span for span in intxt.split("\n\n") if span.strip()]
  
  # WIP
  vs = VisualStanza(stanzas[0])
  vs.to_svg() 