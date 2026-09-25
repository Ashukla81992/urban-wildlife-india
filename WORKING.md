# WORKING — UrbanWildlifeWebsite

## Env
- Hugo extended static site
- Python watermark/metadata scripts

## Run
```bash
cd UrbanWildlifeWebsite
# brew install hugo
hugo server --buildDrafts
# http://localhost:1313
# photo tooling
python3 scripts/watermark.py
python3 scripts/apply_metadata.py
```

## Scripts
| script | purpose | command |
|---|---|---|
| `hugo.toml` | Hugo config | `hugo server --buildDrafts` |
| `scripts/watermark.py` | bake watermark into photos | `python3 scripts/watermark.py` |
| `scripts/apply_metadata.py` | apply metadata | `python3 scripts/apply_metadata.py` |
| `scripts/fill_metadata.py` | fill metadata | `python3 scripts/fill_metadata.py` |
| `raw_photos/` | drop originals here | `then process + content/` |

## Notes
- Needs Hugo extended ≥ 0.157.
- Live: ashukla81992.github.io/urban-wildlife-india
- verified: scaffolded 2026-09-18 (commands taken from repo scripts/README; run once to confirm)
