# smartthings.htm.bridge

> ## Work in Progress

A bridge for smartthings apps to post data to, which will in turn run data through HTM REST API.

## To Run

    pip install -r requirements.txt

You must have the following env vars:

```bash
INFLUX_HOST=localhost
INFLUX_PORT=8086
INFLUX_USER=username
INFLUX_PASS=password
```

Run:

    python runapp.py
    
