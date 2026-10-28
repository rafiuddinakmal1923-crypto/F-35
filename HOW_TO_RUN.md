# How to run VoltGuard AI (and share it with a public link)

This is a step-by-step guide for a Windows 10/11 laptop. Everything runs in Docker, so you don't need
Python or Node.js on the laptop. Commands go in **PowerShell**, from the project folder.

> **R0 uses simulated data and fake personal details only.** Never put real customer data in it.

---

## 1. What you need (one time)

| Item | Notes |
| --- | --- |
| Windows 10/11, 16 GB RAM recommended | 8 GB works with the AI model off (`LLM_MODE=mock`) |
| About 15 GB free disk | Docker images and the database. Drive D: is fine; see step 2 |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Use the WSL 2 backend (the default) |
| [Git for Windows](https://git-scm.com/download/win) | To download and update the code |
| Internet connection | Only for downloads, the map background and the public link |

## 2. Set up Docker (one time)

1. Install Docker Desktop and start it. Wait until the bottom-left corner says **Engine running**.
2. *(Optional)* Move Docker's storage to drive D: in Docker Desktop: **Settings → Resources → Advanced →
   Disk image location**.
3. Give Docker enough memory. Paste this into PowerShell (for a 16 GB laptop; on 8 GB use
   `memory=6GB`):

   ```powershell
   @"
   [wsl2]
   # leave about 4 GB for Windows
   memory=12GB
   swap=8GB
   "@ | Set-Content -Path "$env:USERPROFILE\.wslconfig" -Encoding ascii
   wsl --shutdown
   ```

   Then start Docker Desktop again.

## 3. Get the code (one time)

```powershell
cd "C:\Users\<you>\Desktop\coding"
git clone https://github.com/rafiuddinakmal1923-crypto/F-35.git
cd F-35
git checkout claude/practical-clarke-t5uwrc
```

PowerShell blocks scripts by default. Allow them for this window (repeat in each new window):

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

## 4. First start

```powershell
.\make.ps1 demo
```

This one command:
1. creates `.env` with strong random passwords (never commit this file);
2. builds and starts the containers;
3. sets up the database, loads the simulated network and runs detection;
4. prints the **demo steps and every test account's password**.

The first run takes 10–20 minutes because of the downloads. Later runs take about a minute.

Then open **http://localhost:8080** and sign in with an account it printed.

### Who is who

| Account | Role | Lands on | Can do |
| --- | --- | --- | --- |
| `manager.cen`, `manager.nor` | Revenue Protection Manager | Network overview | Zone-level dashboard, weekly summary, second approval of reports, assistant |
| `analyst.cen`, `analyst2.cen`, `analyst.nor` | Analyst | My work | Zones, suspects, premises, claim cases, approve report content, assistant |
| `supervisor.cen`, `supervisor.nor` | Supervisor | My work | Run the case job, approve dispatch, assign teams, team routes, Telegram chat, sign out a lost phone |
| `inspector.a`, `inspector.b`, `inspector.c` | Field inspector | **Phone app** `…/#/field` | Today's route, case address, record outcomes with photos offline, messages, assistant |
| `datasci` | Data scientist | Models | Run detection, retrain, alerts |
| `admin` | Admin | Data manager | Upload data, settings, audit, sign out phones |
| `auditor` | Auditor | Audit log | Read the tamper-evident log |

Accounts ending `.cen` see the Central region only; `.nor` see Northern only.

**Phone app:** on a phone, open `<your address>/#/field` and sign in as an inspector. It needs an
**https** address (see section 6) because it encrypts case data on the phone. `localhost` works only on
the laptop itself.

## 5. Everyday commands

| I want to… | Command |
| --- | --- |
| Start everything (data is kept) | `.\make.ps1 up` |
| Stop everything (data is kept) | `.\make.ps1 down` |
| Reset the demo and print the steps and passwords again | `.\make.ps1 demo` |
| Get the latest code | `git stash` then `git pull origin claude/practical-clarke-t5uwrc` then `.\make.ps1 build` then `.\make.ps1 up` |
| See what the server is doing | `.\make.ps1 logs` |
| List all commands | `.\make.ps1 help` |
| Run the automated tests | `.\make.ps1 test` |

Useful settings in `.env` (edit with Notepad, then run `.\make.ps1 up`; it gives the AI model the
graphics card when the laptop has an NVIDIA GPU, which plain `docker compose up -d` does not):

| Setting | Use |
| --- | --- |
| `WEB_PORT=8080` | Change it (e.g. `8081`) if another program already uses 8080, then open `http://localhost:8081` |
| `DB_HOST_PORT=15432` | Database port for Power BI; change it if it is taken |
| `LLM_MODE=mock` or `ollama` | `mock` = no AI model needed. For `ollama`, first run `.\make.ps1 models` (about 5 GB) |
| `REPORT_MODE=predrafted` or `live` | `live` = the AI writes the report assessment during the demo; use it only with a GPU, and keep `predrafted` as the fallback |
| `TELEGRAM_BOT_TOKEN=` | Optional real Telegram bot (README "Telegram dispatch bot"). Without it the bot runs inside the app |

---

## 6. Make it a public, clickable link (instead of localhost)

`localhost` works only on your own laptop. To let judges, teammates or an inspector's phone open the app,
use a **Cloudflare Tunnel**. It gives an `https://` link to the app running on your laptop:
- no router settings, no public IP, nothing to install on Windows;
- only the web entry point is exposed (the database and the AI model are not);
- the laptop must stay **on, awake and online** while people use the link.

Before any public link:
- Use the generated passwords. Never use simple ones.
- Change them if you shared them anywhere: delete the `DEMO_PASSWORDS` line in `.env` and run
  `.\make.ps1 demo` again.

### Option A: quick link, no account (good for testing and a same-day demo)

```powershell
.\make.ps1 tunnel
```

After about 10–30 seconds it prints:

```
Public link: https://some-random-words.trycloudflare.com  (written to PUBLIC_BASE_URL; api restarted so case links use it)
```

- Open that link on any device. The phone app is at `https://some-random-words.trycloudflare.com/#/field`.
- Case links in messages (and in Telegram) now use this address.
- The command checks the link from your laptop before saying **OK: the public link works**.
- **Keep it running.** Every restart gives a new random address, which breaks phone sign-ins and links
  already sent. The command keeps a running quick tunnel; if its link is broken, `.\make.ps1 tunnel -New`
  replaces it.
- `.\make.ps1 demo` prints the live address, and clears it if the quick tunnel has stopped.
- No uptime guarantee. It is fine for testing; for judging use Option B.

### Option B: stable link on your own domain (best for judging)

You need a free Cloudflare account and a domain on Cloudflare, either one you already own or a cheap one
bought there.

1. Go to the Cloudflare dashboard → **Zero Trust** → **Networks** → **Tunnels** → **Create a tunnel**.
2. Choose **Cloudflared** and name it `voltguard`.
3. On the install page, **copy the token**: the long text after `--token`. You don't need to install
   anything; Docker runs it.
4. Under **Public hostname**, set:
   - Subdomain: e.g. `voltguard`;
   - Domain: your domain;
   - Service type: **HTTP**;
   - URL: `proxy:80` (exactly this: it is the app's entry point inside Docker).
5. Open `.env` in Notepad and set (use your own values):

   ```
   TUNNEL_TOKEN=eyJhIjoi...the token you copied...
   TUNNEL_HOSTNAME=voltguard.yourdomain.com
   ```

   The token is a secret: keep it only in `.env`, never in chat or Git.
6. Start it:

   ```powershell
   .\make.ps1 tunnel-token
   ```

   It prints `Public link: https://voltguard.yourdomain.com`. That address stays the same every time.

**Optional: only invited people can open it.** In Zero Trust → **Access** → **Applications** → **Add an
application** → *Self-hosted*:
- domain: your hostname;
- policy: *Allow* the judges' e-mail addresses.

Visitors then get a one-time code by e-mail before they reach the sign-in page.

*(Advanced alternative: `.\make.ps1 tunnel-named` with a config file. See
`deploy/cloudflared/config.example.yml`.)*

### Stop sharing

```powershell
.\make.ps1 tunnel-stop
```

The app keeps running on the laptop; the public link stops working and case links point back to the laptop.

### Demo-day checklist for a public link

- [ ] Laptop plugged in; sleep turned off (**Settings → System → Power → Screen and sleep → Never**).
- [ ] `.\make.ps1 demo` run in the morning, and the passwords noted somewhere safe.
- [ ] Tunnel started **once** (Option B preferred) and the link opened on a phone over mobile data.
- [ ] Inspector signed in on the phone through the public link, not `localhost`.

---

## 7. When something goes wrong

| What you see | What to do |
| --- | --- |
| `running scripts is disabled on this system` | `Set-ExecutionPolicy -Scope Process Bypass`, then run the command again |
| `failed to connect to the docker API … dockerDesktopLinuxEngine` | Docker Desktop isn't running. Start it and wait for **Engine running**. If it keeps stopping: `wsl --shutdown`, restart Docker Desktop, check `.wslconfig` memory is below your RAM |
| `ports are not available … 8080` | Another program uses 8080. Find it with `Get-Process -Id (Get-NetTCPConnection -LocalPort 8080 -State Listen).OwningProcess`. If it's `TNSLSNR` (Oracle) or anything you need, add `WEB_PORT=8081` to `.env` and run again |
| `ports are not available … 15432` (or 5432) | Add `DB_HOST_PORT=25432` (any free number) to `.env` |
| `git pull`: *Your local changes would be overwritten* | `git stash`, then pull again |
| Image download is very slow (`ollama`) | It's about 2 GB; let it finish, or stop it with Ctrl+C and run again (it resumes) |
| Map area is grey or says *Map background unavailable* | The laptop can't reach the map servers (CARTO, OpenStreetMap or Esri). Check the internet, VPN or firewall. Zones and routes are still shown |
| Phone app says the data was wiped | It was signed out remotely, or the data was older than 24 hours. Sign in again |
| Browser: *Hmmm… can't reach this page*, `DNS_PROBE_FINISHED_NXDOMAIN` on a `trycloudflare.com` link | The address is stale or not known yet. Run `.\make.ps1 tunnel`: it checks the link and says which problem it is. If it says the tunnel isn't connected, run `.\make.ps1 tunnel -New` for a fresh address. If it says this network's DNS doesn't know it, run `ipconfig /flushdns`, wait a minute, try a phone on mobile data, or turn off antivirus "web protection" for a moment |
| `No tunnel address yet` | Run `docker compose --profile tunnel logs tunnel` and check the laptop is online. Office networks sometimes block Cloudflare tunnels; try a phone hotspot |
| Cloudflare **Error 1033** *Cloudflare Tunnel error* on the link | The tunnel has not connected yet. Wait one minute and reload. The tunnel uses HTTP/2 over port 443, which most networks allow; if the logs (`docker compose --profile tunnel logs tunnel`) keep showing `Failed to dial`, the network blocks Cloudflare: use a phone hotspot |
| Public link opens but case links in messages show `localhost` | Restart the tunnel command; it writes `PUBLIC_BASE_URL` in `.env` and restarts the API |
| Anything else | `.\make.ps1 logs` and send a screenshot of the red error lines |

## 8. More documents

- `README.md`: overview, services, data modes, status and open TNB questions.
- `DEMO.md`: the 7-step demo script.
- `docs/REVIEW_AND_TEST_REPORT.md`: test results.
- `docs/UI_UX_DESIGN_REQUIREMENTS.md`: the design brief.
- `powerbi/BUILD_WITH_CLAUDE_ON_LAPTOP.md`: the Power BI dashboard.
- `HANDOFF.md`: for developers continuing the build.
