import sys
from argparse import ArgumentParser, ArgumentTypeError
from itertools import chain, repeat, islice
from typing import Iterable
from drawsvg import *

from trees import read_wordlines

# default measures
SPACE_LEN = 15
DEFAULT_WORD_LEN = 20
CHAR_LEN = 1.8
NORMAL_TEXT_SIZE = 16
TINY_TEXT_SIZE = 10
SCALE = 5
ARC_BASE_YPOS = 30

class VisualStanza:
  """class to visualize a CoNNL-U stanza; partly corresponding to Dep in the
  Haskell implementation. 
  NOTE: unlike token IDs, positions are counted from 0, hence the -1s"""
  def __init__(self,stanza):
    wordlines = [wl for wl in read_wordlines(stanza.split("\n")) 
                 if wl.ID.isdigit()] # ignore tokens whose ID is not an int

    # token-wise info to be visualized (form + pos), cf. Dep's tokens
    self.tokens = [({"form": wl.FORM, "pos": wl.POS}) for wl in wordlines] 
      
    # list of dependency relations: [((from,to), label)], cf. Dep's deps
    self.deprels = [
      ((int(wl.ID) - 1, int(wl.HEAD) - 1), wl.DEPREL) for wl in wordlines
      if int(wl.HEAD)] # 

    # root position, cf. Dep's root
    self.root = int([wl.ID for wl in wordlines if wl.HEAD == "0"][0]) - 1
  
  def token_width(self, i):
    """total i-th token width (including space) in the output SVG"""
    abs_token_len = CHAR_LEN * max( # cf. Dep's wordLength
      0, 
      len(self.tokens[i]["form"]), 
      len(self.tokens[i]["pos"]))
    rel_token_len = abs_token_len / DEFAULT_WORD_LEN # cf. rwdl
    return 100 * rel_token_len + SPACE_LEN

  def token_xpos(self, i): 
    """start x coordinate of i-th token, cf. wpos"""
    return sum([self.token_width(j) for j in range(i)])
  
  def token_dist(self, a, b):
    """distance between two tokens with positions a and b"""
    return sum([self.token_width(i) for i in range(min(a, b), max(a, b))])
  
  def arcs(self):
    """helper method to extract bare arcs (pairs of positions) form deprels
    NOTE: arcs are extracted ltr, but I don't know if this is really needed"""
    return [(min(src, trg), max(src, trg)) for ((src, trg),_) in self.deprels]

  def arc_height(self, src, trg):
    """height of the arc between src and trg, cf. aheight"""

    def depth(a,b):
      # projective arcs "under" a-b
      sub_arcs = [(x,y) for (x,y) in self.arcs() 
                  if (a < x and y <= b) or (a == x and y < b)]
      if sub_arcs:
        return 1 + max([0] + [depth(x,y) for (x,y) in sub_arcs]) 
      return 0
    
    return depth(min(src,trg), max(src,trg)) + 1
  
  def to_svg(self):
    """generate svg tree code"""
    tokens_w = sum([self.token_width(i) for i in range(len(self.tokens))])
    spaces_w = SPACE_LEN * (len(self.tokens) - 1)

    # picture dimensions 
    tot_w = tokens_w + spaces_w
    tot_h = 55 + 20 * max([0] + [self.arc_height(src,trg) 
                                 for (src,trg) in self.arcs()])
    
    svg = Drawing(tot_w,tot_h, origin=(0,0))
    
    # draw tokens (forms + pos tags)
    for (i,token) in enumerate(self.tokens):
      x = self.token_xpos(i)
      y = tot_h - 5
      svg.append(Text(token["form"], NORMAL_TEXT_SIZE, x=x, y=y))
      svg.append(Text(token["pos"], TINY_TEXT_SIZE, x=x, y=tot_h-20))

    # draw deprels (arcs + labels)
    for ((src,trg),label) in self.deprels:
      # otherwise everything will be mirrored
      ycorrect = lambda y: (round(tot_h)) - round(y) - 5
      
      dxy = self.token_dist(src, trg)
      ndxy = 100 * 0.5 * self.arc_height(src,trg)
      w = dxy - (600 * 0.5) / dxy
      h = ndxy / (3 * 0.5)
      r = h / 2
      x = self.token_xpos(min(src,trg)) + (dxy/2) + (20 if trg < src else 10)
      y = ARC_BASE_YPOS
      x1 = x - w / 2
      x2 = min(x, (x1 + r))
      x4 = x + w / 2
      x3 = max(x, (x4 - r))
      y1 = ycorrect(y)
      y2 = ycorrect(y + r)

      # draw arc
      arc_path = Path(stroke='black', fill='none')
      arc_path.M(x1, y1).Q(x1, y2, x2, y2).L(x3,y2).Q(x4, y2, x4, y1)
      svg.append(arc_path)

      # draw arrow
      x_arr = x + (w / 2) if trg < src else x - (w / 2)
      y_arr = ycorrect(y - 5)
      arrow = Lines(
        x_arr, y_arr, 
        x_arr - 3, y_arr - 6, 
        x_arr + 3, y_arr - 6, 
        stroke="black", fill="black", close="true")
      svg.append(arrow)

      # draw label
      x_lab = x - (len(label) * 4.5 / 2)
      y_lab = ycorrect((h / 2) + ARC_BASE_YPOS + 3)
      svg.append(Text(label, TINY_TEXT_SIZE, x=x_lab, y=y_lab))

    # draw root arrow & text
    x_root_line = self.token_xpos(self.root) + 15
    y_root_line = ycorrect(tot_h)
    root_len = tot_h - ARC_BASE_YPOS
    root_line = Line(
      x_root_line, y_root_line, 
      x_root_line, y_root_line + root_len, 
      stroke="black")
    svg.append(root_line)
    arrow_endpoint = y_root_line + root_len
    root_arrow = Lines(
      x_root_line, arrow_endpoint, 
      x_root_line - 3, arrow_endpoint - 6, 
      x_root_line + 3, arrow_endpoint - 6, 
      stroke="black", fill="black", close="true")
    svg.append(root_arrow)
    svg.append(Text(
      "root", 
      TINY_TEXT_SIZE, 
      x=x_root_line + 5, y=ycorrect(tot_h - 15)))

    return svg


def conll2svg(intxt: str) -> Iterable[str]:

    stanzas = [span for span in intxt.split("\n\n") if span.strip()]
  
    yield '<html>\n<body>\n'
    for stanza in stanzas:
        svg = VisualStanza(stanza).to_svg()
        yield svg.as_svg()
    yield '</body>\n</html>'


if __name__ == "__main__":
    intxt = sys.stdin.read()
    for line in conll2svg(intxt):
        print(line)

