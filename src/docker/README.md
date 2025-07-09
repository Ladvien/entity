# Docker Setup

This image installs Python 3.12, Poetry, all project dependencies and Node.js. It runs all programmatic checks during the build.

Build the image:

```bash
docker build -f src/docker/Dockerfile -t entity-test .
```

Run the tests in the container:

```bash
docker run --rm entity-test
```
