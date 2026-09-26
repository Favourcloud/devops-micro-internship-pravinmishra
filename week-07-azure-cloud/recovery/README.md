# Week 07 recovery source

The [evidence index](../evidence/2026-09-26/README.md) records the actual deployment. Generators define the dedicated 66-resource A4/A5/A6 lab and separate 18-resource A3 exercise. The latter was deleted after verification. Generated state, plans and credentials stay outside Git.

`build_infrastructure.py /private/path` writes Terraform JSON; copy `bootstrap.sh` there. Terraform 1.13.5 and AzureRM 4.47.0 are pinned. Supply subscription, SSH public key, current controller CIDR and protected database/application/JWT inputs privately. **Terraform state contains Key Vault secret values despite sensitive variable markings.** Protect it and never publish it. Resource names/region are specific to this lab; review and adapt them before another deployment. This is not an instruction to duplicate the running lab.

`book-source/` is the exact reviewed source snapshot transferred to the five lab hosts. Web nodes build with `NEXT_PUBLIC_API_URL=/api`; app nodes run the backend. It incorporates earlier reviewed Book Review changes and the Azure adaptations in `azure-runtime.patch`: certificate verification, controlled initialization, generic errors, shared homepage API path and consistent contrast. `book-server.js` is also included in that snapshot.

EpicBook starts from the [Week 09 pinned release](../../week-09-ansible/epicbook-prod/app-patches/README.md), upstream `763becebb8d3f5663a76bb30facddc25be63cfd5`. The two `epic-overrides/` files replace its server and layout: bind to localhost, authenticate without repeated schema changes and display the correct Week 07 banner. Retain the signed-cart/transactional demo-checkout patch. The [Epic manifest](../evidence/2026-09-26/epic-source-manifest.json) covers every deployed file, including unchanged assets.

`initialize-databases.js` performs one-time schema/catalogue initialization with separately protected administrative credentials. Normal services have CRUD-only privileges: Book Review uses `bookreview` from the app subnet; EpicBook uses `bookstore` from 10.0.1.10. Do not run it against unrelated databases.

`load-keyvault-secrets.py` retrieves two secrets using managed identity and writes a root-only environment file without printing values. Install both `week07-app-secrets.service` and `week07-app.service`: the separate oneshot unit is required because systemd loads `EnvironmentFile` before an app's `ExecStartPre`. `book-web.nginx` forwards `/api` to the private API load balancer; Next.js listens on localhost.

The final manifests match the actual installed files. The patch is a change trail, not a universal upstream patch; use the final snapshots/overrides for reproduction. HTTP/browser actions were checked against independent SQL; network isolation and web-node availability were tested separately.
