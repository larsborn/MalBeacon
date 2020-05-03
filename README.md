# MalBeacon Client
Python-based client for the [malbeacon.com] API.

## Installation
Requires at least Python 3.7 and the package `requests` to be installed. For fancy terminal formatting, you'll also 
need `terminaltables`. Fully compatible with being run in a virtual environment.

## Example Usage
After aliasing the script `malbeacon.py` to `malbeacon` and setting the environment variable `MALBEACON_API_KEY` to the 
value from your [malbeacon.com] profile, a typical session may look like the following:

```Batch
$ malbeacon cookie abcdefghijklmnopqrstuvwxyz
| Timestamp  | IP              | URL                                                                   |
|------------|-----------------|-----------------------------------------------------------------------|
| 2020-04-26 | XXX.XX.XX.XXX   | http://example.com/abc/hear.php?some=report&amp;aqGp=view&amp;id=9    |
| 2020-04-26 | XXX.XX.XX.XXX   | http://example.com/abc/hear.php?some=report                           |
| 2020-04-26 | XXX.XXX.XXX.XXX | http://example.com/abc/hear.php?some=report                           |
| 2020-04-28 | XXX.XX.XX.XXX   | http://example.com/abc/hear.php?some=report                           |
| 2020-04-28 | XXX.XXX.XXX.XX  | http://example.com/abc/hear.php?some=report                           |
| 2020-04-28 | XXX.XXX.XXX.XX  | http://example.com/abc/hear.php?some=report&amp;aqGp=flush&amp;rid=16 |
| 2020-04-28 | XXX.XXX.XXX.XX  | http://example.com/abc/hear.php?some=report&amp;aqGp=view&amp;id=13   |
| 2020-04-28 | XXX.XX.XX.XXX   | http://example.com/abc/hear.php?some=bot                              |
| 2020-04-28 | XXX.XX.XX.XXX   | http://example.com/abc/hear.php?some=report                           |
...
| 2020-05-02 | XXX.XX.XX.XXX   | http://example.com/abc/hear.php?some=report                           |
| 2020-05-02 | XXX.XX.XX.XXX   | http://example.com/abc/hear.php?some=report&amp;aqGp=flush&amp;rid=43 |
| 2020-05-03 | XXX.XXX.XX.XXX  | http://example.com/abc/hear.php?some=report&amp;aqGp=flush&amp;rid=43 |
| 2020-05-03 | XXX.XXX.XX.XXX  | http://example.com/abc/hear.php?some=report                           |

User-Agents:
    Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36

First Active: 2020-04-26 05:22:53
Last Active: 2020-05-03 07:05:37

Time of day histogram:
 0: oooooooooooooooo (9)
 2: ooooooooooooooooooo (11)
 3: ooooooo (4)
 4: ooooooooooooooooooooooo (13)
 5: oooooooooooooooooooooooooooooooooooooooo (23)
 6: ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo (37)
 7: oooooooooooooooooooooooooo (15)
 8: ooooooooooooooooooooo (12)
 9: oooooooooooooooooooooooooooooo (17)
10: oooooooooooooo (8)
11: ooooooooooooooooooooo (12)
12: ooooooo (4)
13: oooooooooooooooooooooooooooooooooooooooooooo (25)
14: oooooooooooo (7)
15: oo (1)
16: oo (1)
18: ooooooo (4)
19: oooooooooooooooooo (10)
20: oo (1)
21: oo (1)
22: ooooooooo (5)
23: oooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo (40)
[INFO] Some data was for clarity reasons, specify --json to dump everything.

$ malbeacon --json cookie abcdefghijklmnopqrstuvwxyz > actor-info.json
```


[malbeacon.com]: https://malbeacon.com/
