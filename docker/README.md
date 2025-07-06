# Docker Setup

This image installs Python 3.12, Poetry, all project dependencies and Node.js. It runs all programmatic checks during the build.

Build the image:

```bash
docker build -t entity-test docker
```

Run the tests in the container:

```bash
docker run --rm entity-test
```
