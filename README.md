# GoOutSafe - RestaurantsService

## Running the code

Building the Docker images:

```
$ ./run.sh docker-build
```

Without Docker:

```
$ ./run.sh setup
```

### Unit tests
```
$ ./run.sh unittests
```
#### Unit tests with coverage report
```
$ ./run.sh unittests-report
```
#### Unit tests inside docker
```
$ ./run.sh docker unittests
```
Or with report:
```
$ ./run.sh docker unittests-report
```

### Running in production mode
Docker:
```
$ ./run.sh docker PROD
```
Without Docker:
```
$ ./run.sh PROD
```

### Running in testing mode (with test data and mocks)
Docker:
```
$ ./run.sh docker TEST
```
Without Docker:
```
$ ./run.sh TEST
```
### Running in testing mode (without mocks)
Docker:
```
$ ./run.sh docker FAILURE_TEST
```
Without Docker:
```
$ ./run.sh FAILURE_TEST
```

### Running with Custom configurations
Docker:
```
$ ./run.sh docker MY_CONFIG
```
Without Docker:
```
$ ./run.sh MY_CONFIG
```