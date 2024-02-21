import nltk

sentence = "The large man ate a red apple under a small bridge."
tokens = nltk.word_tokenize(sentence)
tagged = nltk.pos_tag(tokens)
entities = nltk.chunk.ne_chunk(tagged)
grammar = r"""
            NP: {<DT|PP\$>?<JJ>*<NN.*>+} # noun phrase
            PP: {<IN><NP>}               # prepositional phrase
            VP: {<MD>?<VB.*><NP|PP>}     # verb phrase
            CLAUSE: {<NP><VP>}           # full clause
        """
cp = nltk.RegexpParser(grammar)
result = cp.parse(entities)
result.pretty_print()
