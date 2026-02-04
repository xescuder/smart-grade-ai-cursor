# Security Policy

## Security Best Practices

### API Keys and Secrets

**Never commit API keys, tokens, or secrets to the repository.** This is critical for maintaining the security of your application and preventing unauthorized access.

#### Best Practices

- **Use environment variables** for all sensitive configuration
- **Keep `.env` files in `.gitignore`** (already configured in this repository)
- **Use placeholder values** in documentation and example code (e.g., `YOUR_API_KEY_HERE`, `your_api_key_here`)
- **Rotate any exposed keys immediately** if they are accidentally committed
- **Review code before committing** to ensure no secrets are included
- **Use secret scanning tools** in your CI/CD pipeline

### What to Do If You Expose a Secret

If you accidentally commit an API key, token, or other secret to the repository:

1. **Revoke the exposed key immediately** at the provider's website
   - For Google AI API keys: https://aistudio.google.com/apikey
   
2. **Generate a new key** to replace the revoked one

3. **Update your local `.env` file** with the new key

4. **Remove the key from current files** by replacing it with a placeholder

5. **Remove the key from git history** - the secret remains in git history even after removing it from current files. See `REMOVE_SECRET_FROM_HISTORY.md` for detailed instructions.

6. **Notify all collaborators** to:
   - Pull the latest changes
   - Re-clone the repository if history was rewritten
   - Update their local `.env` files with the new key

### Environment Configuration

This repository uses environment variables for sensitive configuration:

```bash
# backend/.env (DO NOT commit this file)
GOOGLE_AI_API_KEY=your_actual_api_key_here
GOOGLE_AI_MODEL=gemini-2.0-flash-exp
DATABASE_URL=your_database_url_here
# ... other sensitive configuration
```

The `.gitignore` file is already configured to exclude:
- `.env`
- `.env.local`
- `.env.*.local`
- Other environment files

### Reporting Security Vulnerabilities

If you discover a security vulnerability in this project, please report it by:

1. **Do not** open a public GitHub issue
2. Contact the repository maintainers directly
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before public disclosure

## Additional Resources

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Git Security Best Practices](https://git-scm.com/book/en/v2/GitHub-Account-Administration-and-Security)
