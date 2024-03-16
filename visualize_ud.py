import sys
from argparse import ArgumentParser, ArgumentTypeError
from itertools import chain, repeat, islice

from drawsvg import *

from trees import read_wordlines

# default measures
SPACE_LEN = 10
DEFAULT_WORD_LEN = 20
CHAR_LEN = 1.8
NORMAL_TEXT_SIZE = 16
TINY_TEXT_SIZE = 10
SCALE = 5
ARC_BASE_YPOS = 30

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
  
  def relative_word_length(self, i): # cf. rwld
    return self.word_length(i) / DEFAULT_WORD_LEN

  def word_size(self, i): # cf. wsize
    return 100 * self.relative_word_length(i) + SPACE_LEN
  
  # start x coordinate of i-th word, cf. wpos
  def word_xpos(self, i): 
    return sum([self.word_size(j) for j in range(i)])
  
  # distance between two words x and y
  def word_dist(self, x, y):
    return sum([self.word_size(i) for i in range(min(x,y), max(x,y))])
  
  def arcs(self):
    return [(min(src,trg), max(src,trg)) for ((src,trg),_) in self.deprels]
  
  # depth of the link from src to trg
  def depth(self,src,trg):
    # projective arcs "under" (src,trg)?
    sub_arcs = [(x,y) for (x,y) in self.arcs() 
                if (src < x and y <= trg) or (src == x and y < trg)]

    if sub_arcs:
      return 1 + max([0] + [self.depth(x,y) for (x,y) in sub_arcs])
    return 0

  # abs height of the arc between nodes with positions src and trg?
  def arc_height(self, src, trg): # cf. aheight
    return self.depth(min(src,trg), max(src,trg)) + 1
  
  def to_svg(self):
    words_width = sum([self.word_size(i) for i in range(len(self.tokens))])
    spaces_width = SPACE_LEN * (len(self.tokens) - 1)
    tot_w = words_width + spaces_width
    tot_h = 50 + 20 * max([0] + [self.arc_height(src,trg) for (src,trg) in self.arcs()])
    svg = Drawing(tot_w,tot_h, origin=(0,0))
    
    # draw tokens (froms + pos tags)
    for (i,token) in enumerate(self.tokens):
      x = self.word_xpos(i)
      y = tot_h
      svg.append(Text(token["form"], NORMAL_TEXT_SIZE, x=x, y=y))
      svg.append(Text(token["pos"], TINY_TEXT_SIZE, x=x, y=tot_h-15))

    # draw deprels (arcs + labels)
    for ((src,trg),label) in self.deprels:
      dxy = self.word_dist(src, trg)
      ndxy = 100 * 0.5 * self.arc_height(src,trg)
      w = dxy - (600 * 0.5) / dxy
      h = ndxy / (3 * 0.5)
      r = h / 2
      x = self.word_xpos(min(src,trg)) + (dxy / 2) + (20 if x < y else 10) # some centering magic
      y = ARC_BASE_YPOS
      ycorrect = lambda y: (round(tot_h)) - round(y)
      x1 = x - w / 2
      x2 = min(x, (x1 + r))
      x4 = x + w / 2
      x3 = max(x, (x4 - r))
      y1 = ycorrect(y)
      y2 = ycorrect(y + r)
      path = Path(stroke='black', fill='none')
      path.M(x1, y1)
      path.Q(x1, y2, x2, y2)
      path.L(x3,y2)
      path.Q(x4, y2, x4, y1)
      svg.append(path)
      print(x1,y1) # TODO: rm
    svg.save_html("example.html")


if __name__ == "__main__":
  intxt = sys.stdin.read()
  stanzas = [span for span in intxt.split("\n\n") if span.strip()]
  
  # WIP
  vs = VisualStanza(stanzas[0])
  vs.to_svg() 