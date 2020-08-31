# :rocket: #GitHubActionsTip 29 :rocket:

A lot of CI systems give you the ability to cancel redundant builds if there has been a newer push to a branch.

This action lets you do that and saves you precious build minutes when pushing to development branches.

Link: https://github.com/marketplace/actions/workflow-run-cleanup-action
```yaml
name: CI
on:
  push: []
  jobs:
    cleanup-runs:
      runs-on: ubuntu-latest
      steps:
      - uses: rokroskar/workflow-run-cleanup-action@master
        env:
          GITHUB_TOKEN: "${{ secrets.GITHUB_TOKEN }}"
      if: "!startsWith(github.ref, 'refs/tags/') && github.ref != 'refs/heads/master'"
    # ...
    other-jobs:
      # ...
```