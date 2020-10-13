Start Elasticsearch
```
$ cd $ELASTICSEARCH_HOME
$ ./bin/elasticsearch
```

Run Alpakka example:
```
$ sbt "run-main dzlab.ElasticAlpakka"
```

You can verify the index “alpakka” creation in Elasticsearch by listing indices in the browser:
```
$ curl http://localhost:9200/_cat/indices\?v
health status index        uuid                   pri rep docs.count docs.deleted store.size pri.store.size
yellow open   iris-alpakka RHTGCE3PSD2rf6uaYYMeKg   1   1        150            0     17.1kb         17.1kb
```

If the index “iris-alpakka” is listed you can see the data in Elasticsearch:
```
$ curl http://localhost:9200/iris-alpakka/_search?pretty
{
  "took" : 4,
  "timed_out" : false,
  "_shards" : {
    "total" : 1,
    "successful" : 1,
    "skipped" : 0,
    "failed" : 0
  },
  "hits" : {
    "total" : {
      "value" : 150,
      "relation" : "eq"
    },
    "max_score" : 1.0,
    "hits" : [
      {
        "_index" : "iris-alpakka",
        "_type" : "_doc",
        "_id" : "USEjIHUBTTUbuCko7OOM",
        "_score" : 1.0,
        "_source" : {
          "f1" : 1.0,
          "f2" : 5.1,
          "f3" : 3.5,
          "f4" : 1.4,
          "label" : "Iris-setosa"
        }
      },
      {
        "_index" : "iris-alpakka",
        "_type" : "_doc",
        "_id" : "UiEjIHUBTTUbuCko7OPf",
        "_score" : 1.0,
        "_source" : {
          "f1" : 2.0,
          "f2" : 4.9,
          "f3" : 3.0,
          "f4" : 1.4,
          "label" : "Iris-setosa"
        }
      },
      {
        "_index" : "iris-alpakka",
        "_type" : "_doc",
        "_id" : "UyEjIHUBTTUbuCko7OPf",
        "_score" : 1.0,
        "_source" : {
          "f1" : 3.0,
          "f2" : 4.7,
          "f3" : 3.2,
          "f4" : 1.3,
          "label" : "Iris-setosa"
        }
      },
      {
        "_index" : "iris-alpakka",
        "_type" : "_doc",
        "_id" : "VCEjIHUBTTUbuCko7OPf",
        "_score" : 1.0,
        "_source" : {
          "f1" : 4.0,
          "f2" : 4.6,
          "f3" : 3.1,
          "f4" : 1.5,
          "label" : "Iris-setosa"
        }
      },
      {
        "_index" : "iris-alpakka",
        "_type" : "_doc",
        "_id" : "VSEjIHUBTTUbuCko7OPf",
        "_score" : 1.0,
        "_source" : {
          "f1" : 5.0,
          "f2" : 5.0,
          "f3" : 3.6,
          "f4" : 1.4,
          "label" : "Iris-setosa"
        }
      },
      {
        "_index" : "iris-alpakka",
        "_type" : "_doc",
        "_id" : "ViEjIHUBTTUbuCko7OPf",
        "_score" : 1.0,
        "_source" : {
          "f1" : 6.0,
          "f2" : 5.4,
          "f3" : 3.9,
          "f4" : 1.7,
          "label" : "Iris-setosa"
        }
      },
      {
        "_index" : "iris-alpakka",
        "_type" : "_doc",
        "_id" : "VyEjIHUBTTUbuCko7OPf",
        "_score" : 1.0,
        "_source" : {
          "f1" : 7.0,
          "f2" : 4.6,
          "f3" : 3.4,
          "f4" : 1.4,
          "label" : "Iris-setosa"
        }
      },
      {
        "_index" : "iris-alpakka",
        "_type" : "_doc",
        "_id" : "WCEjIHUBTTUbuCko7OPf",
        "_score" : 1.0,
        "_source" : {
          "f1" : 8.0,
          "f2" : 5.0,
          "f3" : 3.4,
          "f4" : 1.5,
          "label" : "Iris-setosa"
        }
      },
      {
        "_index" : "iris-alpakka",
        "_type" : "_doc",
        "_id" : "WSEjIHUBTTUbuCko7OPf",
        "_score" : 1.0,
        "_source" : {
          "f1" : 9.0,
          "f2" : 4.4,
          "f3" : 2.9,
          "f4" : 1.4,
          "label" : "Iris-setosa"
        }
      },
      {
        "_index" : "iris-alpakka",
        "_type" : "_doc",
        "_id" : "WiEjIHUBTTUbuCko7OPf",
        "_score" : 1.0,
        "_source" : {
          "f1" : 10.0,
          "f2" : 4.9,
          "f3" : 3.1,
          "f4" : 1.5,
          "label" : "Iris-setosa"
        }
      }
    ]
  }
}
```

Clean up and delete the index
```
$ curl -XDELETE http://localhost:9200/iris-alpakka 
{"acknowledged":true}
```
