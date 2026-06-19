# `stylist`

Stylist CLI for managing Kubernetes-based Salonmaster deployments.

**Usage**:

```console
$ stylist [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `cluster`: Cluster management commands
* `database`: Manage the secrets database
* `proxy`: Proxy applications from the cluster

## `stylist cluster`

Cluster management commands

**Usage**:

```console
$ stylist cluster [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-e, --environment [tst|acc|prd]`: The environment to use (tst, acc, prd)  [env var: STYLIST_ENV; default: tst]
* `-k, --kubeconfig PATH`: Path to the kubeconfig file (local path or `s3://bucket/object`)  [env var: KUBECONFIG; default: ~/.kube/config]
* `-s, --secrets-db PATH`: Path to the secrets database file (supports local paths or `s3://bucket/object`)  [env var: STYLIST_SECRETS_DB]
* `-p, --secrets-db-password TEXT`: Password for the secrets database  [env var: STYLIST_SECRETS_DB_PASSWORD]
* `--help`: Show this message and exit.

**Commands**:

* `bootstrap`: Bootstrap the cluster for the specified...
* `reset`: Reset the cluster and remove its...
* `status`: Get information about the state of the cluster
* `info`: Show detailed information about the cluster

### `stylist cluster bootstrap`

Bootstrap the cluster for the specified environment.

**Usage**:

```console
$ stylist cluster bootstrap [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `stylist cluster reset`

Reset the cluster, remove its configuration, Vault RBAC objects, and any CRDs installed during bootstrap.

**Usage**:

```console
$ stylist cluster reset [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `stylist cluster status`

Get information about the state and health of the cluster. It reports the
current cluster environment and checks each application namespace for failed
deployments.

**Usage**:

```console
$ stylist cluster status [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `stylist cluster info`

Show static detailed information about the cluster. For each application
namespace it lists the chart version and the services deployed there.

**Usage**:

```console
$ stylist cluster info [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `stylist database`

Manage the secrets database

**Usage**:

```console
$ stylist database [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `verify`: Verify that a secrets database exists and...
* `create`: Create a new encrypted secrets database.
* `set`: Insert or update a secret in the database.
* `cluster-credentials`: Store the PostgreSQL cluster credentials secret.
* `remove`: Remove a secret from the database.
* `gui`: Open an interactive editor for the secrets database.
* `changepassword`: Change the encryption password of the secrets database.

### Using S3-compatible storage for the secrets DB

Stylist can transparently work with secrets databases stored in S3 or S3-compatible object stores (Hetzner, MinIO, etc.). Provide an `s3://bucket/key` via `--secrets-db` (or `SECRETS_DB`). Stylist downloads the SQLite file to a secure temporary location, applies your changes, and uploads it back when finished.

Set the standard AWS environment variables to point Stylist to your object store (these are shared with the kubeconfig helper):

| Variable | Description |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | Access key used for the S3-compatible API. |
| `AWS_SECRET_ACCESS_KEY` | Matching secret key. |
| `AWS_SESSION_TOKEN` | Optional session token for temporary credentials. |
| `AWS_REGION` / `AWS_DEFAULT_REGION` | Region that hosts the bucket. |
| `AWS_S3_ENDPOINT` (or `AWS_ENDPOINT_URL`) | Optional custom endpoint for S3-compatible APIs (Hetzner, MinIO, etc.). |

Any command that accepts `--secrets-db` (including `stylist database gui`) can use these URLs, so you can edit credentials locally without manually downloading/uploading the database.

### Fetching kubeconfig files from S3

The `--kubeconfig` option also understands `s3://bucket/object` URLs. Stylist downloads the kubeconfig to a secure temporary location, points `KUBECONFIG` to the cached copy, and removes it once the CLI exits. This works for both `stylist cluster` and `stylist proxy` commands.

Stylist reuses the same AWS environment variables listed above for kubeconfig downloads, so there is no need for any additional `KUBECONFIG_*` settings. Once those are in place you no longer need to pre-download kubeconfigs before running Stylist locally or inside CI.

### `stylist database verify`

Verify that a secrets database exists and can be opened.

**Usage**:

```console
$ stylist database verify [OPTIONS] [DB]
```

**Arguments**:

* `[DB]`: Path to the secrets database

**Options**:

* `-p, --password TEXT`: Database password  [env var: STYLIST_DB_PASSWORD]
* `--help`: Show this message and exit.


### `stylist database create`

Create a new encrypted secrets database.

**Usage**:

```console
$ stylist database create [OPTIONS] [PATH]
```

**Arguments**:

* `[PATH]`: Path of the database to create

**Options**:

* `-p, --password TEXT`: Password for the database  [env var: STYLIST_DB_PASSWORD]
* `--show-password`: Show the generated password  [env var: STYLIST_SHOW_PASSWORD]
* `--help`: Show this message and exit.

### `stylist database set`

Insert or update a secret in the database.

**Usage**:

```console
$ stylist database set [OPTIONS] [DB] [NAMESPACE] [NAME]
```

**Arguments**:

* `[DB]`: Path to the secrets database
* `[NAMESPACE]`: Kubernetes namespace
* `[NAME]`: Secret name

**Options**:

* `-k, --key TEXT`: Secret data key  [env var: STYLIST_SECRET_KEY; default: value]
* `-v, --value TEXT`: Secret value  [env var: STYLIST_SECRET_VALUE]
* `-e, --environment [tst|acc|prd]`: Environment  [env var: STYLIST_ENV]
* `-p, --password TEXT`: Database password  [env var: STYLIST_DB_PASSWORD]
* `--help`: Show this message and exit.

### `stylist database cluster-credentials`

Create or update the `cluster-credentials` secret that backs the PostgreSQL HA chart.
The command writes both the `password` and `repmgr-password` keys for the selected
environment (or for all environments when `--environment` is omitted).

**Usage**:

```console
$ stylist database cluster-credentials [OPTIONS] [DB]
```

**Arguments**:

* `[DB]`: Path to the secrets database

**Options**:

* `-p, --password TEXT`: Database password  [env var: STYLIST_DB_PASSWORD]
* `-e, --environment [tst|acc|prd]`: Environment that should receive the secret
* `--cluster-password TEXT`: Password for the PostgreSQL superuser (prompts if omitted)
* `--repmgr-password TEXT`: Password for the `repmgr` user (prompts if omitted)
* `--namespace TEXT`: Namespace portion of the Vault path  [default: database-system]
* `--name TEXT`: Secret name stored in Vault  [default: cluster-credentials]
* `--help`: Show this message and exit.

### `stylist database remove`

Remove a secret from the database.

**Usage**:

```console
$ stylist database remove [OPTIONS] [DB] [NAMESPACE] [NAME]
```

**Arguments**:

* `[DB]`: Path to the secrets database
* `[NAMESPACE]`: Kubernetes namespace
* `[NAME]`: Secret name

**Options**:
* `-k, --key TEXT`: Secret data key  [env var: STYLIST_SECRET_KEY; default: value]

* `-e, --environment [tst|acc|prd]`: Environment  [env var: STYLIST_ENV]
* `-p, --password TEXT`: Database password  [env var: STYLIST_DB_PASSWORD]
* `--help`: Show this message and exit.


### `stylist database gui`

Open a Textual-based GUI to browse, add, update, and delete secrets from the database. The editor shows secrets in a sortable table and a detail panel for the active record.

**Usage**:

```console
$ stylist database gui [OPTIONS] [DB]
```

**Arguments**:

* `[DB]`: Path to the secrets database

**Options**:

* `-p, --password TEXT`: Database password  [env var: STYLIST_DB_PASSWORD]
* `-e, --environment [tst|acc|prd]`: Pre-select an environment filter  [env var: STYLIST_ENV]
* `--shared-only`: Show secrets without an environment by default
* `--help`: Show this message and exit.

### `stylist database changepassword`

Change the encryption password for the secrets database. Works with both local files and `s3://` URLs.

**Usage**:

```console
$ stylist database changepassword [OPTIONS] [DB]
```

**Options**:

* `--old-password TEXT`: Current password (defaults to `SECRETS_DB_PASSWORD`)
* `--new-password TEXT`: New password (required)
* `--confirm-password TEXT`: Optional confirmation for safety
* `--help`: Show this message and exit


## `stylist proxy`

Proxy common web interfaces from the cluster to your local machine.

**Usage**:

```console
$ stylist proxy [OPTIONS] COMMAND
```

**Options**:

* `--no-browser`: Skip opening the browser (by default a browser window opens)
* `--help`: Show this message and exit.

**Commands**:

* `vault`: Proxy the Vault UI
* `argocd`: Proxy the ArgoCD interface
* `keycloak`: Proxy Keycloak
* `dashboard`: Proxy the Kubernetes dashboard
* `grafana`: Proxy Grafana
