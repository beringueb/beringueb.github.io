# Self-hosting my website on a solar-powered Raspberry Pi

As of 5 November 2026. Live, editable version: <https://claude.ai/artifact/PsQv6Vv8UDK5Q4Ah4hydjH>

## Overview

The website can move from GitHub Pages to the Raspberry Pi Zero 2 W at home in an afternoon (Part 1), then run off a 50 W panel and a ~150 Wh LiFePO4 battery (Part 2). Do Part 1 on mains power first, measure the Pi's real consumption, then size the solar kit from that number.

**Already done.** The site is a Hugo static site: `hugo --minify` writes plain files to `public/`, which any web server can serve. The Pi only serves files; it never builds anything.

**Why it is realistic.** [solar.dri.es](https://solar.dri.es/) runs on the same board, a Pi Zero 2 W, with a 50 W panel and an 18 Ah LiFePO4 battery. It measures 0.4 W idle and 1.3 W under load. [Low-tech Magazine](https://solar.lowtechmagazine.com/about/the-solar-website/) ran at 1–2.5 W on a 30–50 W panel and was online 95.3% of a year.

**Before going solar, shrink the site.** It builds to 9.8 MB today, mostly four images. `images/cmb.png` (4.4 MB) is the favicon, so every visit downloads it. `perso_velo.jpg` (1.5 MB), `cmb_round.jpeg` (1.7 MB) and `cmb_8bits.jpg` (0.7 MB) should become ~50–100 KB each.

## Part 1 — Self-host on the Pi Zero 2 W

Done looks like this: `https://<your-domain>` is served by the Pi over the Freebox, with HTTPS, and the GitHub Pages copy stays online as a backup. Everything below runs on mains power.

### What you need

| Item | Why | Note |
| --- | --- | --- |
| Raspberry Pi Zero 2 W | The server | Already owned. Wi-Fi is 2.4 GHz only |
| microSD, 16–32 GB, "high endurance" A1/A2 | Survives constant writes and power cuts | A cheap card is the usual failure point |
| 5 V 2.5 A micro-USB supply | Power for Part 1 | Replaced by the solar kit later |
| USB power meter | Measure the real watts before buying solar parts | Around €10–15 (approximate) |
| Domain name | `beringueb.github.io` cannot point at your home | Around €10/year at a French registrar (approximate) |

### 1. Install the OS

1. In Raspberry Pi Imager, pick **Raspberry Pi OS Lite (64-bit)**.
2. In the customisation screen, set hostname `solar`, your user, **SSH with public key only**, your Wi-Fi, Wi-Fi country **FR**, time zone Europe/Paris.
3. Boot, then from the laptop: `ssh <user>@solar.local`.
4. Update and keep it updated:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y unattended-upgrades
```

### 2. Cut power use and SD-card writes

Add to `/boot/firmware/config.txt`, then reboot:

```
dtoverlay=disable-bt
camera_auto_detect=0
display_auto_detect=0
dtparam=act_led_trigger=none
dtparam=act_led_activelow=on
```

Keep logs in RAM: set `Storage=volatile` and `RuntimeMaxUse=16M` in `/etc/systemd/journald.conf`. If `free -h` shows swap, turn it off (on Bookworm: `sudo systemctl disable --now dphys-swapfile`).

### 3. Serve the site with Caddy

Caddy gets and renews HTTPS certificates by itself; solar.dri.es uses it on the same board.

```bash
sudo apt install -y caddy
sudo mkdir -p /var/www/site && sudo chown $USER /var/www/site
```

`/etc/caddy/Caddyfile` (use `:80 {` instead of the domain line to test on the home network first):

```
<your-domain>, www.<your-domain> {
    root * /var/www/site
    file_server
    encode zstd gzip
    header /images/* Cache-Control "public, max-age=2592000"
    header /assets/* Cache-Control "public, max-age=2592000"
}
```

Then `sudo systemctl reload caddy`.

### 4. Deploy from the laptop

First set `baseURL = "https://<your-domain>/"` in `hugo.toml`. Then each update is one line from the repo:

```bash
hugo --minify && rsync -avz --delete public/ <user>@solar.local:/var/www/site/
```

### 5. Open the Freebox to the Pi

1. **Fixed local address.** In Freebox OS (`http://mafreebox.freebox.fr`) → Paramètres de la Freebox → DHCP → Baux statiques: reserve an address for the Pi, e.g. `192.168.1.50`.
2. **Full-stack IPv4.** By default Free shares one IPv4 address between several subscribers, so ports 80 and 443 cannot be forwarded. In the subscriber area (espace abonné), request the free "adresse IP fixe V4 full-stack" option, then reboot the Freebox. This step comes from user reports, not Free's documentation ([forum](https://www.nas-forum.com/forum/topic/68515-configuration-des-ports-avec-la-freebox-pop)).
3. **Port forwarding.** Freebox OS → Paramètres → Gestion des ports: TCP 80 → Pi port 80, TCP 443 → Pi port 443. Never forward SSH (22).
4. **Test from outside.** On a phone using mobile data, open `http://<your public IP>`; it should show the site.

The full-stack address is fixed, so no dynamic-DNS script is needed (solar.dri.es needs one because its address changes).

### 6. Domain, DNS and HTTPS

1. At the registrar, add `A` records for `@` and `www` pointing to the Freebox public IPv4.
2. Free also gives IPv6. Add an `AAAA` record to the Pi's global IPv6 only after checking that the Freebox IPv6 firewall lets 80/443 through; until then, IPv4 alone is fine.
3. Switch the Caddyfile back to the domain line and reload. Caddy fetches the Let's Encrypt certificate on its own; watch it with `journalctl -u caddy -f`.

### 7. Security

No exposed server is 100% safe, but a static site behind two forwarded ports is low-risk. The real danger is a taken-over Pi reaching the other devices at home, so the steps below aim at that.

**What is exposed.** Only TCP 80 and 443, to Caddy serving plain files: no PHP, database or login page, and Caddy runs as its own unprivileged user. The remaining risks:

| Risk | What could happen | Fix |
| --- | --- | --- |
| A flaw in Caddy or Linux | An attacker controls the Pi, inside your home network | Isolate the Pi; block it from the home network; automatic updates |
| IPv6 | Every home device has a public address | Keep the Freebox IPv6 firewall on |
| UPnP on the Freebox | Any device at home can open ports by itself | Turn UPnP off |
| DMZ or extra forwards | Everything on one device is exposed | DMZ off; only 80 and 443 forwarded |
| Freebox remote access | Router settings reachable from the internet | Off, or a strong password |
| Public home IP | Location roughly visible; a flood can slow your internet | Accept it, or use a tunnel (below) |

**On the Pi: incoming traffic.** SSH from the home network only, web from anywhere:

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp
sudo ufw allow 80,443/tcp
```

**On the Pi: outgoing traffic.** Stop the Pi from opening connections to other home devices, except the Freebox (its gateway and DNS). ufw uses the first rule that matches, so the allow comes first:

```bash
sudo ufw allow out to 192.168.1.254
sudo ufw deny out to 192.168.1.0/24
sudo ufw enable
sudo ufw status numbered
```

Replies still flow, so SSH and rsync from the laptop keep working. These rules stop an attacker who gets in through Caddy's unprivileged user; they do not stop one who gets root. Use your Freebox's real address if it is not `192.168.1.254`. Leave the Pi on IPv4 only, or IPv6 would bypass these rules.

**On the Pi: updates and listeners.**

- Check that security updates install themselves: `sudo unattended-upgrade --dry-run --debug` and `/var/log/unattended-upgrades/`.
- `sudo ss -tlnp` should list only 22, 80 and 443 open to the network (Caddy's admin port 2019 must show `127.0.0.1` only).

**On the Freebox (Freebox OS, advanced mode).**

- UPnP IGD: off.
- DMZ: off.
- Port forwarding: only TCP 80 and 443 to the Pi.
- Remote access to Freebox OS: off, or a long unique password.
- IPv6 firewall: on, in the IPv6 settings. If your model has no such switch, do not publish an AAAA record.

**Isolate the Pi (strongest step).** Put the Pi on its own network so that even root on the Pi cannot see your laptop or phone. Two options:

1. Freebox guest Wi-Fi: guest devices cannot see the home network. I could not confirm that port forwarding reaches a guest device, so test it before relying on it.
2. A small second router in front of the Pi: the Freebox forwards 80/443 to that router, which forwards them to the Pi. The Pi only sees the second router's network.

**Check from outside.** From a laptop on phone tethering (not the home Wi-Fi), `nmap -Pn <your public IP>` should show only 80 and 443 open. Re-check after any Freebox update.

**Alternative with no open port.** A Cloudflare Tunnel makes the Pi connect out to Cloudflare, so nothing is forwarded and your IP stays hidden. The cost is depending on Cloudflare, which partly defeats the self-hosting goal.

### 8. Keep GitHub Pages as the backup

Keep the GitHub Actions deploy: `beringueb.github.io` stays up when the Pi is offline. Link to it in the footer ("mirror"). DNS cannot switch over automatically without a paid failover service, so the low-tech choice is to accept short outages, as both reference sites do.

## Part 2 — Run it on solar power

A 50 W panel and a 12 V 12 Ah LiFePO4 battery (about 154 Wh) keep a ~1 W Pi online all year in Paris, according to PVGIS. A 30 W panel works too if a few offline days in November and January are acceptable.

### 1. Measure first

Put the USB power meter between the supply and the Pi for a week of normal use and note the average watts. Expect 0.4–1.3 W, as on solar.dri.es. Add about 15% for the 12→5 V converter and the charge controller's own use. The sizing below assumes 24 Wh/day (1 W) and checks 36 Wh/day (1.5 W).

### 2. Size the panel and battery

Results from the EU's PVGIS off-grid simulator for Paris (weather 2005–2023, panel facing south, battery never below 20%). "Vertical" is a panel hung on a balcony railing.

| Panel | Battery | Mount | Use per day | Days the battery runs empty, whole year | Nov / Dec / Jan |
| --- | --- | --- | --- | --- | --- |
| 50 W | 154 Wh | tilted 35° | 24 Wh | 0% | 0 / 0 / 0% |
| 50 W | 154 Wh | vertical | 24 Wh | 0% | 0 / 0 / 0% |
| 50 W | 154 Wh | vertical | 36 Wh | 1.2% | 6 / 1 / 6% |
| 50 W | 77 Wh | vertical | 24 Wh | 0.8% | 4 / 0 / 4% |
| 30 W | 154 Wh | vertical | 24 Wh | 0.3% | 2 / 0 / 1% |
| 30 W | 154 Wh | vertical | 36 Wh | 6.9% | 27 / 11 / 25% |
| 30 W | 77 Wh | vertical | 24 Wh | 3.4% | 13 / 7 / 13% |

PVGIS assumes no shading. A balcony facing other buildings gets less sun, so rerun the [PVGIS off-grid tool](https://re.jrc.ec.europa.eu/pvg_tools/en/) with your exact address before buying. For scale, a 50 W panel in Paris makes about 70–80 Wh a day in December and about 220 Wh in June.

### 3. Parts list

| Part | Suggested choice | Why |
| --- | --- | --- |
| Solar panel | 50 W, 12 V monocrystalline | Same as solar.dri.es; 30 W if space is short |
| Charge controller | Small 12 V MPPT with a data port, e.g. Victron SmartSolar MPPT 75/10 | Its VE.Direct port lets the Pi read the battery level over USB; its load output cuts power when the battery is low |
| Battery | 12.8 V, 12 Ah LiFePO4 with built-in BMS | Long life, safe indoors. Pick one that refuses to charge below 0 °C if it lives outside |
| 12 V → 5 V converter | Buck converter, 3 A, micro-USB output | The Pi Zero 2 W takes 5 V on micro-USB |
| Fuse | Inline fuse on the battery's + wire | Rating as given in the controller's manual |
| Cables | MC4 leads for the panel, VE.Direct-to-USB cable | |

All-in-one alternative: solar.dri.es uses a Voltaic LiFePO4 battery with the MPPT controller built in, which removes the separate controller.

### 4. Wire it in this order

```
 Off-grid solar kit                                        |
 +------------+  12 V  +------------------+  load output  +-------------+  5 V USB  +---------------+
 | Solar panel| -----> | MPPT controller  | ------------> | 12 V -> 5 V | --------> | Pi Zero 2 W   |
 | 50 W, 12 V |        | e.g. Victron     |               | buck, 3 A   |           | Caddy, ~1 W   |
 +------------+        +------------------+               +-------------+           +---------------+
                              ^   |                                                        | Wi-Fi
                    charge /  |   v discharge                          Mains power         v
                       +-------------------+                                       +---------------+
                       | LiFePO4 battery   |                                       | Freebox       |
                       | 12.8 V, ~154 Wh   |                                       | fwd 80 + 443  |
                       +-------------------+                                       +---------------+
                                                                                           | full-stack IPv4
                                                                                           v
                                                                                   +---------------+
                                                                                   | Internet      |
                                                                                   +---------------+
```

Only the Pi runs on the sun: the battery sits behind the controller, which feeds the Pi through its load output; the Freebox and the rest of the network stay on mains power, as on solar.dri.es.

1. Battery to controller first (through the fuse), so the controller detects 12 V.
2. Then the panel to the controller.
3. Then the controller's load output to the 5 V converter, and the converter to the Pi.
4. To take it apart, go in the reverse order: Pi, panel, battery.

Keep the battery and the Pi indoors if you can, with only the panel outside. Low-tech Magazine does the same.

### 5. Survive running out of power

- **Clean shutdown.** A small script reads the battery level from the controller every few minutes (VE.Direct is a plain-text serial protocol) and runs `sudo shutdown -h now` below about 15%.
- **Automatic restart.** Set the controller's load output to switch off a little below that level and back on at about 40%. The Pi boots by itself when power returns.
- **Protect the SD card.** Turn on the read-only overlay: `sudo raspi-config` → Performance Options → Overlay File System. A sudden cut then cannot corrupt the card. Turn it off when you update the system, since updates are lost on reboot while it is on.

### 6. Show the battery level on the site

Both reference sites publish their battery state. Have the same script write `status.json` (battery %, charging or not, uptime) into `/var/www/site/` every 10 minutes, and add a few lines of JavaScript to the footer to display it. Add `--exclude status.json` to the rsync deploy so it is not deleted.

## Checklist

- [ ] Shrink the four large images (favicon first)
- [ ] Buy a high-endurance microSD, a USB power meter and a domain
- [ ] Flash Raspberry Pi OS Lite 64-bit with SSH key and Wi-Fi
- [ ] Trim config.txt, logs in RAM, swap off
- [ ] Install Caddy, test on the home network
- [ ] Set `baseURL`, deploy with rsync
- [ ] Freebox: static DHCP lease, full-stack IPv4, forward 80 and 443
- [ ] DNS A records and HTTPS through Caddy; security: ufw in and out, UPnP and DMZ off, IPv6 firewall on, isolate the Pi, outside port scan
- [ ] Footer link to the GitHub Pages mirror
- [ ] Measure the Pi's watts for a week
- [ ] Rerun PVGIS for the exact balcony, then buy panel, controller, battery, converter, fuse
- [ ] Wire battery → panel → load, in that order
- [ ] Shutdown script, load-output thresholds, read-only overlay
- [ ] Publish status.json on the site

## Sources

- [solar.dri.es](https://solar.dri.es/): Pi Zero 2 W, 50 W panel, 18 Ah LiFePO4, Caddy, port forwarding; 0.4 W idle, 1.3 W load
- [Low-tech Magazine, About the solar website](https://solar.lowtechmagazine.com/about/the-solar-website/): 1–2.5 W server, 30 W panel, 168 Wh battery, 95.3% uptime over a year
- [PVGIS](https://re.jrc.ec.europa.eu/pvg_tools/en/) (EU Joint Research Centre): solar output and off-grid simulations for Paris, SARAH3 data 2005–2023
- [NAS-Forum thread on Freebox ports](https://www.nas-forum.com/forum/topic/68515-configuration-des-ports-avec-la-freebox-pop): shared IPv4 and the full-stack option
