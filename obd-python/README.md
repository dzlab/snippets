Install ODB python library
```
$ git clone https://github.com/dailab/python-OBD-wifi
$ cd python-OBD-wifi
$ python -m pip install --upgrade setuptools
```

```python
import obd
import time

connection = obd.OBD("192.168.0.10", 35000)
commands = connection.supported_commands

starttime = time.time()

while True:
  time.sleep(60.0 - ((time.time() - starttime) % 60.0))
  line = {"time": time.strftime("%Y/%m/%d %H:%M:00", time.localtime())}
  for cmd in commands:
    response = connection.query(cmd)
    line[cmd.name] = str(response.value)
  print(line)
```

Download and unzip Elasticsearch - [link](https://www.elastic.co/downloads/elasticsearch)
Download and unzip Kibana - [link](https://www.elastic.co/downloads/kibana)
Start Elasticsearch/Kibana
```
$ cd kibana && bin/kibana
$ cd elasticsearch && bin/elasticsearch
```

Point your browser at http://localhost:5601
