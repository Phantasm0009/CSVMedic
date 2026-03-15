# FAQ

**Why read everything as string first?**  
Pandas’ default type inference can corrupt data: `00742` becomes `742`, and dates can be parsed in the wrong order. Reading as string and then applying our own detection keeps control and avoids silent errors.

**Why not use dateutil.parser or dateparser?**  
They are too permissive (e.g. parsing "hello" as a date) and too slow for batch column analysis. We use `strptime` with explicit format strings for speed and reliability.

**What if my file has no header?**  
The dialect detector tries to infer header presence. You can also pass pandas options via `**pandas_kwargs` (e.g. `header=None` and set column names yourself).

**Can I use csvmedic with Excel (.xlsx)?**  
Install the optional dependency: `pip install csvmedic[excel]`. Support for `.xlsx` can be added in a future release.
