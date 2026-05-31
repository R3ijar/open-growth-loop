# Security Policy

Open Growth Loop is designed to process local CSV files and write local reports. It should not require secrets for its core workflows.

## Reporting Issues

If you find a vulnerability, open a GitHub security advisory or contact the maintainer privately before publishing details.

## Data Boundary

The aggregate event importer only accepts:

```text
date,asset,event,count
```

It rejects private-looking columns such as email, user, session, ip, payload, token, key, secret, sku, phone, name, and file.

Do not add features that require raw user payloads in the core package. Integrations should aggregate data before it reaches Open Growth Loop.
