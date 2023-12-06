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

    def __str__(self):
        return '\t'.join([
            self.ID, self.FORM, self.LEMMA, self.POS, self.XPOS,
            self.FEATS, self.HEAD, self.DEPREL, self.DEPS, self.MISC
            ])

    def feats(self) -> dict:
        featvals = [fv.split('=') for fv in self.FEATS.split('|')]
        return {fv[0]: fv[1] for fv in featvals}

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
    fields = s.split()
    if len(fields) == 10 and fields[0][0].isdigit():
        return WordLine(*fields)
    else:
        raise NotValidWordLine


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


