# Download provenance — CodeTrack

On 16 September 2026 Copilot downloaded the learner's existing course website, rather than choosing an unrelated third-party template. The three HTTPS requests succeeded and `cmp` verified byte equality with `CodeTrack/` at repository commit `0983d638c1139d78bd9a4de18a719626bf89bc9c`. This is source-download evidence, not deployment evidence or a screenshot. No third-party license grant is asserted; this is reuse within the learner's own coursework repository, preserving its attribution.

Immutable source directory: <https://github.com/Favourcloud/devops-micro-internship-pravinmishra/tree/0983d638c1139d78bd9a4de18a719626bf89bc9c/CodeTrack>

| Download | SHA-256 of downloaded original |
|---|---|
| [index.html](https://raw.githubusercontent.com/Favourcloud/devops-micro-internship-pravinmishra/0983d638c1139d78bd9a4de18a719626bf89bc9c/CodeTrack/index.html) | `85f12fada8edce1730aa3aa43a4ed355acb48c5c7e333d9f05ffc23e0179ed94` |
| [contact.html](https://raw.githubusercontent.com/Favourcloud/devops-micro-internship-pravinmishra/0983d638c1139d78bd9a4de18a719626bf89bc9c/CodeTrack/contact.html) | `f843921259ba16c1e33dbf3788699c44ba2f95426b89af79651ca6ae7696d61a` |
| [style.css](https://raw.githubusercontent.com/Favourcloud/devops-micro-internship-pravinmishra/0983d638c1139d78bd9a4de18a719626bf89bc9c/CodeTrack/style.css) | `96f92b381bfdbce824f5103aa1d1cc9b4182c489a02769dcc4dc2186765f5436` |

To reproduce the download without overwriting personalized files, from `static-web/`:

```bash
mkdir -p .local/source
for file in index.html contact.html style.css; do
  curl --fail --silent --show-error --location \
    "https://raw.githubusercontent.com/Favourcloud/devops-micro-internship-pravinmishra/0983d638c1139d78bd9a4de18a719626bf89bc9c/CodeTrack/$file" \
    -o ".local/source/$file"
done
shasum -a 256 .local/source/*
```

Review each checksum against the table before reuse. Changes from the originals: `Favour Eze` becomes `Eze Favour` in both HTML files; the existing CodeTrack/DMI footer is retained and a new paragraph, `Deployed by Eze Favour — Week 09 multi-host lab`, is added. CSS is byte-identical. The footer describes the deployment artifact; it is not a claim that deployment has occurred. Local CSS and the contact link are included, so there are no missing linked assets or JavaScript dependencies. The offline content test checks these transformations against the immutable Git objects, hashes and all relative links.
