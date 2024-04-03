# deptreepy
Python utilities for dependency trees, replicating some of gf-ud.
Designed to work on CoNNL-U data, such as in https://universaldependencies.org

## Installation
Deptreepy requires Python 3. To install dependencies, you can run

```
pip install -r requirements.txt
```

You can now use deptreepy by running

```
python deptreepy.py
```

## Usage

You can start by looking at a quick set of [example uses](./examples.sh)

For a help message: do
```
  $ python3 deptreepy.py
```
You will see this:
```
usage:

   python3 deptreepy.py <command> <arg>*

The command-arg combinations are

   cosine_similarity <file> <file> <field>*  # cosine similarity of treebanks wrt <field>*
   'match_trees <pattern>'           # match entire trees 
   'match_subtrees <pattern>'        # match entire trees and recursively their subtrees
   'match_wordlines <pattern>'       # match individual wordlines in all trees
   'match_segments <pattern>         # match contiguous, disjoint segments of trees
   'change_wordlines <pattern>'      # make changes in wordlines
   'change_subtrees <pattern>'       # change subtrees recursively
   'statistics <field>*'             # frequency-ordered statistics of <field>*
   'treetype_statistics'             # frequency-ordered statistics of types of trees
   'head_dep_statistics'             # frequency-ordered statistics of head-dependent pairs
   'count_wordlines'                 # the number of wordlines
   'count_trees'                     # the number ot trees
   'take_trees <int-from> <int-to>'  # selection of trees
   'underscore_fields <field>*'      # replace values of <field>* with _
   'extract_sentences'               # return FORM sequences as one-liners
   'trees2conllu'                    # convert internal trees to CoNLLU stanzas
   'trees2wordlines'                 # convert internal trees to a single sequence of wordlines
   'visualize_conllu'                # convert a CoNNLU text into SVG in HTML
   'txt2conllu'                      # parse raw text with UDPipe2 (model config in udpipe2_params.yaml)
   'conllu2trees'                    # convert conllu to deptrees (e.g. to analyse parse result further)
   'from_script <file>'              # read commands from a file

The commands without <file> arguments read CoNLL-U content from std-in,
for example, with the redirection <eng-ud.conllu.
These command can also be piped: for example,

   python3 deptreepy.py 'match_wordlines DEPREL nsubj | statistics POS' <FILE.conllu
   
gives statistics of POS (part of speech) of words that appear as subjects (DEPREL nsubj).
   
The single quotes around the commands where they are used above are
necessary to group the command into one command-line argument.

The <field> arguments correspond to CoNLL-U word line fields from left to right:

    ID FORM LEMMA POS XPOS FEATS HEAD DEPREL DEPS MISC

The following patterns match both wordlines and trees, depending on the command:

   <field>  <strpatt>      # field with its value,      example: LEMMA poli*
   HEAD_DISTANCE <inpred>  # linear distance from head, example: HEAD_DISTANCE >1
   AND <pattern>*          # all patterns patch
   OR  <pattern>*          # at least one of the patterns match
   NOT <pattern>*          # the pattern does not match

When applied to trees, they match the root node of the tree.
The following patterns match only trees:

   LENGTH <intpred>           # number of wordlines in the tree
   DEPTH <intpred>            # depth of the tree
   TREE <pattern> <pattern>*  # <pattern> matches the root, <pattern>* subtrees in sequence
   TREE_ <pattern> <pattern>* # <pattern> matches the root, <pattern>* a subset of subtrees
   SEQUENCE <pattern>*        # <pattern>* matches the sequence of wordlines exactly 
   SEQUENCE_ <pattern>*       # <pattern>* matches a subset of wordlines
   HAS_SUBTREE <pattern>*     # some immediate subtree matches this pattern
   HAS_NO_SUBTREE <pattern>*  # no immediate subtree matches this pattern
   IS_NONPROJECTIVE           # the tree is non-projective

The auxialiary concepts are:

   <strpatt>, a string with *,?,[seq] wildcards (like Unix filenames)
   <intpred>, one of =n, <n, >n, !n, giving a comparison to number n (which can be negative)

For example,

   match_trees SEQUENCE_ (LEMMA politi*)

matches trees that are "about politics", i.e. contain a lemma starting "politi".

   match_subtrees TREE (AND) (HEAD_DISTANCE >0) (HEAD_DISTANCE <0)

matches trees that have both a head-final and a head-initial constituent: `(AND)` is true
of the head, because it poses no conditions on it, the first subtree comes before the head
(has a positive distance to it) and the second one after the head (negative distance).

   match_wordlines FEATS *=In*   # some of the features has value starting In

matches indicative, infinitive, inessive, and other features starting with "In".

Quotes are not used around string patterns: if used, they can only match strings with
actual quotes.

Segments of trees are matched currently with the following patterns:

   REPEAT >?<int> <treepattern>  # <n> contiguous trees matching <treepattern>
   SEGMENT <treepattern>*      # contiguous trees matching <treepattern>* in the given order

Examples:

   match_segments REPEAT >3 (FEATS *=Past*)    # group of more than 3 past tense sentences
   match_segments SEGMENT (AND) (HAS_SUBTREE (AND (DEPREL nsubj) (POS PRON)))  # any sentence followed by one with a pronoun subject

Segments can be useful for discovering narrative structures. But notice that, for many treebanks, segments make no sense,
because they are just bags of sentences (often for copyright reasons).

In addition to search patterns, there are ones that change trees, invoked by the
command change_wordlines:

  <field> <strpatt> <str>        # change values of <field> that match <strpatt> to <str>
  IF <pattern> <changepattern>   # change if the wordline matches <pattern>
  AND <changepattern>*           # perform all these changes in parallel

For example.

  change_wordlines AND (LEMMA the that) (FORM the that)

changes definite articles to the word "that", both in the lemma and the form.

The command change_subtrees admits the following patterns:

  PRUNE <int>                   # drop subtrees below depth <int>
  IF <pattern> <changepattern>  # apply changes in trees that match <pattern>

It traverses each tree recursively top-down: the next step is performed in the tree
resulting from the previoues step.

The Udpipe-2 parser can be called from a pipe and its output converted to trees for further analysis:

  cat FILE.txt | ./deptreepy.py 'txt2conllu | conllu2trees | match_subtrees (POS ADJ)'

The command change_trees only performs the changes in entire trees.
Examples:

  change_trees PRUNE 2   # "summarization" by dropping words below depth 2

To show the results of analysis or changes in plain sentences, use extract_sentences:

  cat FILE.conllu | ./deptreepy.py 'change_trees PRUNE 2 | extract_sentences'

To reconstruct valid CoNLLU trees (with IDs in contiguous sequence, root labelled 'root'),
use trees2conllu

  cat FILE.conllu | ./deptreepy.py 'change_trees PRUNE 2 | trees2conllu'

To visualize dependency trees (as SVG images in an HTML document),

  cat FILE.conllu | ./deptreepy.py 'visualize_conllu' >FILE-trees.html

You can use the Haskell program utils/VisualizeUD.hs, which also has an option to generate LaTeX code,

  cat FILE.conllu | runghc utils/VisualizeUD.hs (latex | svg)

SVG is recommended for non-latin alphabets such as Chinese, unless you have
suitable LaTeX packages available.
```
