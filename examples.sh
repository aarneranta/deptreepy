echo "## make sure FILE.conllu is a CoNLLU file or a link to one"

echo "## statistics on POS of nsubj"
python3 deptreepy.py 'match_wordlines DEPREL nsubj | statistics POS' <FILE.conllu

echo "## sentences where lemma politi* occurs"
cat FILE.conllu | ./deptreepy.py 'match_trees SEQUENCE_ (LEMMA politi*) | extract_sentences'

echo "## subtrees with both head-initial and head-final modifiers"
cat FILE.conllu | ./deptreepy.py 'match_subtrees TREE (AND) (HEAD_DISTANCE >0) (HEAD_DISTANCE <0)'

echo "## subtrees where the head is a noun and it has no determiner" 
cat FILE.conllu | ./deptreepy.py 'match_subtrees (AND (POS NOUN) (HAS_NO_SUBTREE (DEPREL det)))'

echo "## wordlines with feature starting In"
cat FILE.conllu | ./deptreepy.py 'match_wordlines FEATS *=In*'

echo "## any segment followed by one where the subject is a pronoun"
cat FILE.conllu | ./deptreepy.py 'match_segments SEGMENT (AND) (HAS_SUBTREE (AND (DEPREL nsubj) (POS PRON)))'

echo "## segments of 6 or more past tense sentences"
cat FILE.conllu | ./deptreepy.py 'match_segments (REPEAT >6 (FEATS *=Past*)) | trees2conllu'

echo "## change the to that in all wordlines"
cat FILE.conllu | ./deptreepy.py 'change_wordlines AND (LEMMA the that) (FORM the that)'

echo "## summarize sentences by dropping words below depth 2"
cat FILE.conllu | ./deptreepy.py 'change_trees PRUNE 2 | extract_sentences'

echo "## drop words below depth 2 and return valid CoNLLU stanzas"
cat FILE.conllu | ./deptreepy.py 'change_trees PRUNE 2 | trees2conllu'

echo "## extract predicate frames by reading a pattern from a script" 
cat FILE.conllu | ./deptreepy.py 'from_script predicates.oper'

echo "## parse a text file and analyse the result"
cat FILE.txt | ./deptreepy.py 'txt2conllu | conllu2trees | match_subtrees (POS ADJ)'

echo "## visualize trees in SVG"
cat FILE.conllu | ./deptreepy.py 'visualize_conllu' >FILE-trees.html

echo "## visualize the results of pattern matching"
cat FILE.conllu | ./deptreepy.py 'match_trees (POS NOUN) | trees2conllu | visualize_conllu' >FILE-trees.html

