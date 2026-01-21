# how to use pypi

## workflow initial setup

- in your github account, go to the Repository (⚠️ not account settings): `Settings` > `Secrets and variables` > `New secret`
- name the secret `PYPI_API_KEY_CANCERDATA` and paste your pypi token
- workflow is run upon push to `master` branch, as defined in [.github/workflows/publish.yml](.github/workflows/publish.yml)

## manual

**0 init environment after `uv sync`**

```bash
uv pip install twine
```

**1 build changes first**

```bash
rm -r dist/ & uv build
```  

**2 commit and upload changes**

**3 publish**

```bash
py -m twine upload dist/*
```

**combined**

```bash
rm -r dist/ & uv build && py -m twine upload dist/*
```
