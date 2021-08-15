# Spark Jep
Examples running python code from spark scala using [jep](https://github.com/ninia/jep).

Install dependencies: jep, spacy and download a language model
```
$ pip install jep
$ pip install spacy
$ python -m spacy download en_core_web_sm
```

Locate the installation of JEP libraries, one hacky way is to try to load `jep` from a python interpreter:
```
$ python -c "import jep"
Traceback (most recent call last):
  File "/usr/local/share/conda/envs/py3/lib/python3.9/site-packages/jep/__init__.py", line 27, in <module>
    from _jep import *
ModuleNotFoundError: No module named '_jep'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/usr/local/share/conda/envs/py3/lib/python3.9/site-packages/jep/__init__.py", line 29, in <module>
    raise ImportError("Jep is not supported in standalone Python, it must be embedded in Java.")
ImportError: Jep is not supported in standalone Python, it must be embedded in Java.
```

Export the path to jep
```
$ export JAVA_LIBRARY_PATH=/usr/local/share/conda/envs/py3/lib/python3.9/site-packages/jep
```

Run the scala example
```
$ sbt "runMain dzlab.ScalaSpacyExample"
[[The, DET, det], [red, ADJ, amod], [fox, NOUN, nsubj], [jumped, VERB, ROOT], [over, ADP, prep], [the, DET, det], [lazy, ADJ, amod], [dog, NOUN, pobj], [., PUNCT, punct]]
```

Run the Spark example
```
$ sbt "runMain dzlab.SparkSpacyExample"
```

## References
- How Jep Works - [link](https://github.com/ninia/jep/wiki/How-Jep-Works)
- https://github.com/sushant-hiray/scala-python-example
- https://github.com/juand-r/entity-recognition-datasets
- https://github.com/jacoxu/StackOverflow
- https://spark.apache.org/docs/3.1.2/quick-start.html