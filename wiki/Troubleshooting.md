# Troubleshooting

## Common issues

| Problem                                       | Fix                                                                                                                                                                             |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **"This app is blocked"** in browser          | You skipped the OAuth consent screen setup. Go to [Google Cloud Setup](Google-Cloud-Setup) and configure it, adding yourself as a test user.                                    |
| **"Google hasn't verified this app"** warning | Expected for personal projects. Click **Advanced** then **Go to [app name] (unsafe)**.                                                                                          |
| **"Credentials file not found"** error        | Make sure `credentials.json` is in `~/.gdsync/`. See [Google Cloud Setup](Google-Cloud-Setup).                                                                                  |
| **"Token has been expired or revoked"**       | Delete `~/.gdsync/token.json` and run `gdsync` again to re-authorize.                                                                                                           |
| **403 / rate limit errors**                   | gdsync retries automatically with exponential backoff. If persistent, wait a few minutes and try again. You can also increase `rate_limit_delay` in `config.yaml`.              |
| **Some files don't export**                   | Check `~/.gdsync/exceptions.yaml`. Common reasons: file too large, no permission, or file deleted. Remove the entry to retry.                                                   |
| **Huge archive files**                        | Archives include all exported files. If your Drive has many large PDFs/PPTX, archives grow fast. Lower `max_archive_mb` in `config.yaml` or reduce export types with `--types`. |

## Retry failed files

Files that fail to export are added to `~/.gdsync/exceptions.yaml` and skipped on subsequent runs. To retry:

1. Open `~/.gdsync/exceptions.yaml`
1. Remove the entry for the file you want to retry
1. Run `gdsync` again

## Reset everything

To start completely fresh:

```bash
# Remove auth token (will re-prompt for Google sign-in):
rm ~/.gdsync/token.json

# Remove all config and start over:
rm -rf ~/.gdsync

# Remove exported files:
rm -rf ~/Documents/gdsync
```

## Debug logging

Run with `-v` to see exactly what gdsync is doing:

```bash
gdsync -v
```

This shows timestamped DEBUG output including every file being processed, API calls, retries, and skip reasons.
