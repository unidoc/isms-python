# Examples

## Setup

```sh
pip install isms-sdk

export ISMS_API_URL=https://your.isms.sh
export ISMS_API_TOKEN=<api-token>
```

Or point at an env file (`KEY=VALUE` per line, same format the `isms` CLI reads):

```sh
export ISMS_ENV=~/.isms/isms.env
```

## Run

```sh
python examples/add_suppliers.py
```
