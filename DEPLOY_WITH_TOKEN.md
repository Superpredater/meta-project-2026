# 🚀 Deploy to HuggingFace - WITH YOUR TOKEN

You have your token! Now let's deploy.

---

## Option 1: Use the Deployment Script (EASIEST)

**Double-click this file:**
```
deploy_with_token.bat
```

**It will:**
1. Ask for your token
2. Deploy to HuggingFace automatically
3. Guide you if there are issues
4. Show next steps

---

## Option 2: Manual Command Line

Open PowerShell or Command Prompt in this folder:

### If deploying to `openenv/openenv-email-triage`:

```bash
git push https://oauth2:YOUR_TOKEN_HERE@huggingface.co/spaces/openenv/openenv-email-triage main
```

Replace `YOUR_TOKEN_HERE` with your actual token (starts with `hf_`)

### If creating your own Space:

1. Go to: https://huggingface.co/new-space
2. Name: `openenv-email-triage`
3. SDK: **Docker**
4. Visibility: **Public**
5. Create, then run:

```bash
git push https://oauth2:YOUR_TOKEN_HERE@huggingface.co/spaces/YOUR_USERNAME/openenv-email-triage main
```

---

## After Deployment

1. **Wait 2-5 minutes** for HuggingFace to build
2. **Check Space**: https://huggingface.co/spaces/YOUR_USERNAME/openenv-email-triage
3. **Look for**: "Application startup complete" in logs
4. **Test endpoint**:
   ```bash
   curl -X POST https://YOUR_USERNAME-openenv-email-triage.hf.space/reset
   ```
   Should return: `{"status":"ok","message":"..."}`

5. **Run validation**:
   ```bash
   openenv validate openenv-email-triage
   ```
   Should show: ✅ All checks passed

6. **Resubmit Phase 1** - Will be accepted! 🎉

---

## Troubleshooting

**Error: "Repository not found"**
→ Create your own Space first (see above)

**Error: "Authentication failed"**
→ Check token has WRITE permissions

**Error: "Space build failed"**
→ Check build logs on HuggingFace for errors
→ Should not happen - code tested locally ✅

---

## 🎯 Quick Reference

Your token starts with: `hf_`
Get it from: https://huggingface.co/settings/tokens

**Deploy command:**
```bash
git push https://oauth2:TOKEN@huggingface.co/spaces/OWNER/openenv-email-triage main
```

Replace:
- `TOKEN` = your HuggingFace token
- `OWNER` = `openenv` or your username

---

**All code is fixed and ready. Just deploy and resubmit!** 🚀
