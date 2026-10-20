# Deploy to cafemaad.ir

Cafe Maad runs on the same server as datadevvv.ir, behind ArvanCloud:

```
Visitor ─► ArvanCloud CDN (HTTPS) ─► server nginx :80 ─┬─ Host: cafemaad.ir   ─► /var/www/cafemaad/index.html
                                                       └─ Host: datadevvv.ir  ─► (unchanged)
```

| File | Purpose |
|---|---|
| `nginx-cafemaad.conf` | nginx `server` block for cafemaad.ir and www.cafemaad.ir; serves only `index.html` |
| `install.sh` | Clones or updates the repository in `/opt/cafemaad`, publishes the page, installs the nginx site and reloads nginx |

## 1. ArvanCloud

1. At the domain registrar (e.g. nic.ir), set the name servers to `a.ns.arvancdn.ir` and `v.ns.arvancdn.ir`. Wait until the ArvanCloud panel shows the domain as active.
2. **DNS records**: add `A` records for `@` and `www` pointing at the server's IP, with the cloud (proxy) icon turned on.
3. **HTTPS settings**: issue the free certificate, turn on HTTPS and "redirect HTTP to HTTPS". Set the origin protocol to HTTP (the server listens on port 80, as for datadevvv.ir).

## 2. Server

As root:

```bash
git clone --depth 1 https://github.com/basatiamirhossein/Cafe-Maad.git /opt/cafemaad
bash /opt/cafemaad/deploy/install.sh
curl -sI -H 'Host: cafemaad.ir' http://127.0.0.1/ | head -n 1     # HTTP/1.1 200 OK
```

`install.sh` runs `nginx -t` before reloading, so a broken config never takes datadevvv.ir down.

## Updating

After pushing changes to `main` (with a rebuilt `index.html`):

```bash
bash /opt/cafemaad/deploy/install.sh
```

If ArvanCloud caches HTML, purge the cache in the panel after an update.
