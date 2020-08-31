# :rocket: #GitHubActionsTip 27 :rocket:

Creating release notes and changelogs can create a lot of manual and continuous effort.

[@decathlondev](https://twitter.com/decathlondev) created an awesome GitHub Action that automatically creates release notes when you've completed a milestone.

Link: https://github.com/marketplace/actions/release-notes-generator
```yaml
# Trigger the workflow on milestone events
on:
  milestone:
    types: [closed]
name: Milestone Closure
jobs:
  create-release-notes:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@master
    - name: Create Release Notes
      uses: docker://decathlon/release-notes-generator-action:2.0.1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        OUTPUT_FOLDER: temp_release_notes
        USE_MILESTONE_TITLE: "true"
```