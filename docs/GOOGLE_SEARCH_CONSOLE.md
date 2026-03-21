# Google Search Console verification (GitHub Pages)

Property URL should be:

`https://ashukla81992.github.io/urban-wildlife-india/`

## 1. HTML file upload (recommended file name is fixed)

1. In Search Console, choose **HTML file** and **download** the file (e.g. `google623a1e4044f495b1.html`).
2. **Do not change the file name or body** (Google allows only a newline at the end). Replace `static/google623a1e4044f495b1.html` in this repo with that exact file if Google gives you a new one.
3. Push to `main` and wait until **Actions → Deploy to GitHub Pages** finishes (green).
4. In a **private/incognito** window, open:

   `https://ashukla81992.github.io/urban-wildlife-india/google623a1e4044f495b1.html`

   You should see the same text as inside the downloaded file.
5. Click **Verify** in Search Console.

If you still get **file not found**, the live site has not picked up the latest deploy — fix any failing workflow run first.

## 2. HTML tag (optional second method)

This uses a **different** token than the HTML file. In Search Console choose **HTML tag**, copy only the value inside `content="..."`, and set in `hugo.toml`:

```toml
[params]
  googleSiteVerification = "paste_the_exact_token_here"
```

Commit, deploy, then verify. You can keep both file + tag for redundancy.

## Redirects

Search Console **does not follow redirects** for the **HTML file** check. The file must return **200** at the exact URL above (no redirect to another host).
