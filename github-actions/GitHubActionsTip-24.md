# :rocket: #GitHubActionsTip 24 :rocket:

Integration tests are a great way to ensure your application works as expected but they often require additional services like a database or a cache.

You can define services like a redis cache directly in your workflows and access them in your steps.

```yaml
name: Redis container example
on: push
jobs:
  container-job:
    runs-on: ubuntu-latest
    container: node:10.18-jessie
    services:
      redis: # Label used to access the service container
        image: redis
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - name: Connect to Redis
        # Runs a script that creates a Redis client, populates
        # the client with data, and retrieves data
        run: node client.js
        env:
          # The hostname used to communicate with the Redis service container
          REDIS_HOST: redis
          # The default Redis port
          REDIS_PORT: 6379
```

You can read more about setting up these services in GitHub's documentation: https://docs.github.com/en/actions/configuring-and-managing-workflows/about-service-containers