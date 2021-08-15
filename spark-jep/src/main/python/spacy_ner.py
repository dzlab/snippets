import spacy

nlp = spacy.load("en_core_web_sm")

def ner(text):
  doc = nlp(text)
  result = []
  for token in doc:
    result.append((token.text, token.pos_, token.dep_))
  return result