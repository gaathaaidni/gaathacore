from fabric import Connection, task
from pathlib import Path

# Example fabfile to copy .env to remote hosts and restart service

TARGETS = ["server1.example.com", "server2.example.com"]
REMOTE_PATH = "/opt/gaatha/shared/.env"
DEPLOY_USER = "deployuser"
RESTART_CMD = "sudo systemctl restart gaatha.service"


@task
def deploy(c):
    """Run: fab -H host1,host2 deploy --local-path=.env"""
    local_path = c.local_path if hasattr(c, 'local_path') else '.env'
    p = Path(local_path)
    if not p.exists():
        print('.env not found locally')
        return
    for host in TARGETS:
        conn = Connection(host=host, user=DEPLOY_USER)
        conn.put(str(p), '/tmp/gaatha.env.new')
        conn.sudo(f'mv /tmp/gaatha.env.new {REMOTE_PATH}')
        conn.sudo(f'chown gaatha:gaatha {REMOTE_PATH} && chmod 600 {REMOTE_PATH}')
        conn.run(RESTART_CMD)
