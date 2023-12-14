import sys
from dataclasses import dataclass


@dataclass
class WordLine:
    ID: str
    FORM: str
    LEMMA: str
    POS: str
    XPOS: str
    FEATS: str
    HEAD: str
    DEPREL: str
    DEPS: str
    MISC: str

    def as_dict(self):
        return {
          'ID': self.ID, 'FORM': self.FORM, 'LEMMA': self.LEMMA,
          'POS': self.POS, 'XPOS': self.XPOS,
          'FEATS': self.FEATS, 'HEAD': self.HEAD, 'DEPREL': self.DEPREL,
          'DEPS': self.DEPS, 'MISC': self.MISC
          }
    
    def __str__(self):
        return '\t'.join(self.as_dict().values())

    def feats(self) -> dict:
        featvals = [fv.split('=') for fv in self.FEATS.split('|')]
        return {fv[0]: fv[1] for fv in featvals}

WORDLINE_FIELDS = set('ID FORM LEMMA POS XPOS FEATS HEAD DEPREL DEPS MISC'.split())

ROOT_LABEL = 'root'

def ifint(id: str) ->int:
    if id.isdigit():
        return int(id)
    else:
        return int(float(id))  # for ids like '7.1'

    
class NotValidWordLine(Exception):
    pass


class NotValidTree(Exception):
    pass


def read_wordline(s: str) -> WordLine:
    "read a string as a WordLine, fail if not valid"
    fields = s.strip().split('\t')
    if len(fields) == 10 and fields[0][0].isdigit():
        return WordLine(*fields)
    else:
        raise NotValidWordLine

def read_wordlines(lines):
    "read a sequence of strings as WordLines, ignoring failed ones"
    for line in lines:
        try:
            word = read_wordline(line)
            yield word
        except:
            pass
    
    
def statistics(fields, wordlines):
    "frequency table of a combination of fields, as dictionary"
    stats = {}
    for word in wordlines:
        value = tuple(word.as_dict()[field] for field in fields)
        stats[value] = stats.get(value, 0) + 1
    return stats


def sorted_statistics(stats):
    "frequency given as dict, sorted as list in descending order"
    stats = list(stats.items())
    stats.sort(key = lambda it: -it[1])
    return stats


def cosine_similarity(stats1, stats2):
    "cosine similarity between two frequency dictionaries"
    dot = 0
    for k in stats1:
        dot += stats1[k] * stats2.get(k, 0)
    len1 = sum(v*v for v in stats1.values())
    len2 = sum(v*v for v in stats2.values())
    return dot/((len1 ** 0.5) * (len2 ** 0.5)) 


@dataclass
class Tree:
    root: object
    subtrees: list

    def prettyprint(self, level=0, indent=2):
        lines = [level*indent*' ' + str(self.root)]
        level += 1
        for tree in self.subtrees:
            lines.extend(tree.prettyprint(level))
        return lines

    def __len__(self):
        return 1 + sum(map(len, self.subtrees))

    def depth(self):
        if self.subtrees:
            return 1 + max(map(lambda t: t.depth(), self.subtrees))
        else:
            return 1

    
@dataclass
class DepTree(Tree):
    comments: list
    
    def __str__(self):
        lines = self.comments
        lines.extend(self.prettyprint())
        return '\n'.join(lines)

    def wordlines(self):
        words = [self.root]
        for tree in self.subtrees:
            words.extend(tree.wordlines())
        words.sort(key=lambda w: ifint(w.ID))
        return words

    def sentence(self):
        return ' '.join([word.FORM for word in self.wordlines()])
        

    
def build_deptree(ns: list) -> DepTree:
    
    def build_subtree(ns, root):
        subtrees = [build_subtree(ns, n) for n in ns if n.HEAD == root.ID]
        return DepTree(root, subtrees, [])
                           
    try:
        root = [n for n in ns if n.HEAD == '0'][0]
        dt = build_subtree(ns, root)
#        if len(dt) != len(ns):   # 7.1
#            raise NotValidTree
        return dt
    except:
        print(ns)
        raise NotValidTree

    
def relabel_deptree(tree: DepTree) -> DepTree:
    "set DEPREL of head to root and its HEAD to 0, renumber wordlines to 1, 2, ..."
    root = tree.root
    root.MISC = root.MISC + '('+root.DEPREL+')'
    root.DEPREL = 'root'
    words = tree.wordlines()  # sorted by ID
    numbers = {w.ID:  str(i) for w, i in zip(words, range(1, len(words) + 1))}
    numbers[root.HEAD] = '0'

    def renumber(t):
        if t.root.ID.isdigit():
            t.root.ID = numbers[t.root.ID]
        t.root.HEAD = numbers[t.root.HEAD]
        for st in t.subtrees:
            renumber(st)
        return t

    return renumber(tree)


def nonprojective(tree: DepTree) -> bool:
    "if a subtree is not projective, i.e. does not span over a continuous sequence"
    ids = [int(w.ID) for w in tree.wordlines() if w.ID.isdigit()]
    ids.sort()
    return len(ids) == max(ids) - min(ids)

    
def echo_conllu_file(file):
    for line in file:
        try:
            t = read_wordline(line)
            print(t)
        except:
            if not line.strip() or line.startswith('#'):
                print(line.strip())
            else:
                print('INVALID', line)


def conllu_file_trees(file):
    comms = []
    nodes = []
    for line in file:
        if line.startswith('#'):
            comms.append(line.strip())
        elif line.strip():
            t = read_wordline(line)
            nodes.append(t)
        else:
            dt = build_deptree(nodes)
            dt.comments = comms
            yield dt
            comms = []
            nodes = []
            

if __name__ == '__mainz__':
    echo_conllu_file(sys.stdin)


if __name__ == '__main__':
    for dt in conllu_file_trees(sys.stdin):
        print(dt)
        print()


