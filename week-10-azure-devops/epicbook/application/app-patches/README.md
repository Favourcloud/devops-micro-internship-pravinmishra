# Reproducible EpicBook demo patch

This is a disclosed modification of the pinned instructor EpicBook source. It is not represented as unchanged upstream behavior. The patch adds signed per-browser carts, transactional and retry-safe demo checkout, decimal prices, origin checks, sensitive-path restrictions and TLS verification for managed MySQL. No payment or shipment is implemented.

`source-lock.json` pins the upstream revision, patch digest and every resulting source file. `build_release.py --output /private/path/epicbook.tar.gz` checks the patch and resulting file hashes before creating a deterministic archive. Keep generated archives outside the public source tree. The release ID is the patch SHA-256, checked again by deployment.

The real managed deployment and HTTP/SQL results are in the week evidence index. `test_session.cjs` exercises signed-cart validation against the built source; set `DMI_EPICBOOK_SOURCE` to that local source directory before invoking `node --test test_session.cjs`. Secrets and database credentials are supplied separately through encrypted Ansible variables or scoped pipeline secret variables.
