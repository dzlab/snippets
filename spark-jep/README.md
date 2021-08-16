# Spark Jep
Examples running python code from spark scala using [jep](https://github.com/ninia/jep).

Install dependencies: jep, spacy and download a language model
```
$ pip install jep
$ pip install spacy
$ python -m spacy download en_core_web_sm
```

Locate the installation of JEP libraries:
```
$ pip show jep
Name: jep
Version: 3.9.0
Summary: Jep embeds CPython in Java
Home-page: https://github.com/ninia/jep
Author: Jep Developers
Author-email: jep-project@googlegroups.com
License: zlib/libpng
Location: /usr/local/share/conda/envs/py3/lib/python3.9/site-packages
Requires: 
Required-by: 
```

Export the path to jep
```
$ export LD_LIBRARY_PATH=/usr/local/share/conda/envs/py3/lib/python3.9/site-packages/jep
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