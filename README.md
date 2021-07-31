# latency-triangulator-integrator-analysator-7560b
Or short LTIA 7560b<br />

Lets say, you want to see how good the servers are connected (latency) to your existing network.<br />
You can either compare existing + new servers or just the new ones to the rest of your network and pick the best connected one for transit.<br />

You could also just use it as fping remote thingy.

**Prepare**<br />
Rename machina.example.json to machina.json and fill it up<br />

**Examples**<br />

```
python3 7560b.py 1.1.1.1,8.8.8.8
```
