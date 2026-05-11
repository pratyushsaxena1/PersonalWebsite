# personal website

this is my personal website (pratyushsaxena.com). notes for me on how to push updates live.

## deploy

1. push to github:
   ```
   git push origin main
   ```

2. SSH into GoDaddy:
   - godaddy.com → My Products → Web Hosting → Manage → cPanel Admin
   - cPanel → Advanced → Terminal

3. pull and restart:
   ```
   cd ~/finalPersonalWebsite
   git pull origin main
   touch tmp/restart.txt
   ```
