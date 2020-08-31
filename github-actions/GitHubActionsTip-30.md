# :rocket: #GitHubActionsTip 30 :rocket:

Building all projects in a monorepo can be quite time and resource intensive. ⌛

GitHub allows you to define multiple workflows in a single repository and you can specify a number of paths that should have been changed to trigger your workflow.

**first-project.yaml**
```yaml
name: First Project workflow
on:
  - push:
    paths:
    - 'first-project/**'
jobs:
  build:
    name: Build
    runs-on: ubuntu-latest
    steps: [...]
```

**second-project.yaml**
```yaml
name: Second Project workflow
on:
  - push:
    paths:
    - 'second-project/**'
jobs:
  build:
    name: Build
    runs-on: ubuntu-latest
    steps: [...]
```