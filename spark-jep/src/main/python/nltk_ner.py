import nltk
from nltk.stem import WordNetLemmatizer

nltk.download('punkt')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()

def nltk_lemmatizer(text):
  tokens = nltk.word_tokenize(text)
  result = []
  for token in tokens:
    lemmatized = lemmatizer.lemmatize(token)
    result.append((token, lemmatized))
  return result