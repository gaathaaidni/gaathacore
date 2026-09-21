Rotation playbook — rotating SECRET_KEY across production instances

Overview
--------
This playbook documents a safe, manual/automated process to rotate `SECRET_KEY` across one or more production instances.

Prerequisites
- SSH access to each server
- A list of target servers (hostnames) and the deploy user
- Knowledge of how to restart your app (systemd, supervisor, touch WSGI, or PA reload)

High-level plan
1. Generate a new secret locally; back up existing `.env` files.
2. Deploy the new `.env` (or set env var) on all app instances without restarting yet.
3. Restart app instances one at a time (or rolling restart) to pick up new SECRET_KEY.
4. Verify session continuity and login flows; monitor logs.
5. If anything fails, roll back to backed up `.env` files and restart.

Commands (manual)

Generate a new key and write to local `.env` and `instance/.env` (creates backups if rotating):

```bash
python scripts/generate_secret.py --instance
# or to rotate (creates .bak files):
python scripts/rotate_secret.py --out .env
```

Deploy the new `.env` to remote servers (example using `scp`/`ssh`):

```bash
# On operator machine
# Copy new .env to server and move into place atomically
for host in server1.example.com server2.example.com; do
  scp .env deployuser@${host}:/tmp/gaatha.env.new
  ssh deployuser@${host} 'sudo mv /tmp/gaatha.env.new /opt/gaatha/shared/.env && sudo chown gaatha:gaatha /opt/gaatha/shared/.env && sudo chmod 600 /opt/gaatha/shared/.env'
done
```

Restart one app instance and smoke-test:

```bash
ssh deployuser@server1.example.com 'sudo systemctl restart gaatha.service'
# or for PythonAnywhere: use the Web UI reload button
# then test login / session flows
```

Rollback
--------
If something breaks, restore the `.bak` file created by `rotate_secret.py` on the affected server and restart the service:

```bash
# Example: restore backup and restart
ssh deployuser@server1.example.com 'sudo mv /opt/gaatha/shared/.env.bak /opt/gaatha/shared/.env && sudo systemctl restart gaatha.service'
```

Helper scripts
--------------
Use `scripts/apply_secret_via_ssh.sh` to automate scp/ssh deployment of the new `.env` to servers (edit before use).

Notes
- Avoid rotating keys during high-traffic windows if sessions are critical — rotating will invalidate signed cookies/sessions.
- Coordinate across services that rely on the same secret (e.g., multiple app instances, workers).
