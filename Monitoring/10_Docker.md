# Monitoring stack with Docker

## Docker Compose
Create a `docker-compose.yml` file that will bring up Prometheus/AlertManager/Grafana:
```yaml
## docker-compose.yml ##

version: '3'

volumes:
  prometheus_data: {}
  grafana_data: {}

services:

  alertmanager:
    container_name: alertmanager
    hostname: alertmanager
    image: prom/alertmanager
    volumes:
      - ./alertmanager.conf:/etc/alertmanager/alertmanager.conf
    command:
      - '--config.file=/etc/alertmanager/alertmanager.conf'
    ports:
      - 9093:9093
    restart: unless-stopped

  prometheus:
    container_name: prometheus
    hostname: prometheus
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    links:
      - alertmanager:alertmanager
    ports:
      - 9090:9090
    restart: unless-stopped

  grafana:
    container_name: grafana
    hostname: grafana
    image: grafana/grafana
    volumes:
      - ./grafana_datasources.yml:/etc/grafana/provisioning/datasources/all.yaml
      - ./grafana_config.ini:/etc/grafana/config.ini
      - grafana_data:/var/lib/grafana
    ports:
      - 3000:3000
    restart: unless-stopped
```

## Prometheus
### Configure Prometheus itself

Set global config
- `scrape_timeout` is set to the global default (10s).
- Set the scrape interval (`scrape_interval`) to every 15 seconds. Default is every 1 minute.
- Set `evaluation_interval` to periodically evaluate rules every 15 seconds. The default is every 1 minute.

```yaml
## prometheus.yml ##

global:
  scrape_interval:     15s 
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
      - targets: ["alertmanager:9093"]

rule_files:
  - /etc/prometheus/alert_rules.yml

# A scrape configuration containing exactly one endpoint to scrape:
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'prometheus'
    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.
    static_configs:
      - targets: ['prometheus:9090']

  - job_name: 'vad-metrics'
    metrics_path: '/metrics'
    scrape_interval: 5s
    static_configs:
      - targets: ['docker.for.mac.host.internal:9091']
```

### Configure alert rules
Configure the rules once and periodically evaluate them according to the global 'evaluation_interval'.

```yaml
## alert_rules.yml ##

# Alert for any instance that is unreachable for >1 minutes.
groups:
  - name: AllInstances
    rules:
      - alert: InstanceDown
        # Condition for alerting
        expr: up == 0
        for: 1m
        # Annotation - additional informational labels to store more information
        annotations:
          title: 'Instance {{ $labels.instance }} down'
          description: '{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 1 minute.'
        # Labels - additional labels to be attached to the alert
        labels:
          severity: 'critical'
```

## AlertManager
Configure AlertManager notification services in `alertmanager.conf`, in this case using pagerduty
```yaml
## alertmanager.conf ##

global:
  resolve_timeout: 1m
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

route:
  receiver: 'pagerduty-notifications'

receivers:
- name: 'pagerduty-notifications'
  pagerduty_configs:
  - service_key: 0c1cc665a594419b6d215e81f4e38f7
    send_resolved: true
```

## Grafana


### Configure Grafana initialization
Define the place to find startup config

```yaml
## grafana_config.ini ##

[paths]
provisioning = /etc/grafana/provisioning

[server]
enable_gzip = true
```

### Configure Grafana datasources
```yaml
## grafana_datasources.yml ##

apiVersion: 1

# tells grafana where to find prometheus
datasources:
  - name: 'prometheus'
    type: 'prometheus'
    access: 'proxy'
    url: 'http://prometheus:9090'
```

## Manage the monitoring stack

### Start it
```
$ docker-compose up
```

Visit Grafana at http://localhost:3000/  (username/password is `admin`/`admin`)

![image](https://user-images.githubusercontent.com/1645304/139505711-00701e65-439b-4cfc-889f-3b6cbf117c9f.png)


Visit Prometheus at http://localhost:9090/

![image](https://user-images.githubusercontent.com/1645304/139505548-305a033f-2bd8-46ad-8997-4bda7c0f30a9.png)

Visit AlertManager at http://localhost:9093/

![image](https://user-images.githubusercontent.com/1645304/139505833-a04422e3-eeec-436c-b65f-49758f84c4f6.png)


### Stop it
```
$ docker-compose down -v
```


## Resources
- Monitoring Docker Services with Prometheus - [link](https://www.ctl.io/developers/blog/post/monitoring-docker-services-with-prometheus)
- Configure Prometheus and Grafana in Dockers - [link](https://medium.com/aeturnuminc/configure-prometheus-and-grafana-in-dockers-ff2a2b51aa1d)
- Metrics: Reliably Configuring Prometheus and Grafana with Docker - [link](https://levelup.gitconnected.com/metrics-reliably-configuring-prometheus-and-grafana-with-docker-2077541c8e6d)
- Step-by-step guide to setting up Prometheus Alertmanager with Slack, PagerDuty, and Gmail - [link](https://grafana.com/blog/2020/02/25/step-by-step-guide-to-setting-up-prometheus-alertmanager-with-slack-pagerduty-and-gmail/)
- Alerts of the Prometheus Alertmanager with MS Teams - [link](https://lapee79.github.io/en/article/prometheus-alertmanager-with-msteams/)
- [prometheus-grafana-alertmanager-example/docker-compose.yml](https://github.com/PagerTree/prometheus-grafana-alertmanager-example/blob/master/docker-compose.yml)
- New Features in Prometheus 1.4.0 - [link](https://www.robustperception.io/new-features-in-prometheus-1-4-0)
- An Open Source Prometheus Tutorial for System and Docker Monitoring - [link](https://logz.io/blog/prometheus-tutorial-docker-monitoring/)
