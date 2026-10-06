# Contributing

Use fictional or explicitly shareable data. Do not include credentials, personal information, proprietary
source, internal endpoints, conversation archives or runtime databases in issues/PRs.

Python 3.10+, standard library runtime. From a source checkout:

```sh
python -m pip install . ruff
python -m unittest discover -s tests -v
python -m compileall -q agent_mem tests
ruff check .
```

Prefer a narrow reproducible bug fix to a new abstraction. A host adapter needs an isolated install/CLI
check and a clearly identified boundary between deterministic checks and live model behavior. Broader
features should first demonstrate a real unmet need. Contributions use the MIT license; third-party
assets/code require compatible terms and attribution. Never assign a license to users' memory contents.
