# GitHub Domain Setup for Tesla Fleet API

Tesla Fleet API requires a public domain to host a verification file. GitHub Pages provides a free solution that's perfect for this requirement.

## 🎯 **What You'll Create**

A free website at `https://yourusername.github.io` that hosts Tesla's required public key file.

**Time Required:** 10 minutes

---

## 📋 **Prerequisites**

- GitHub account (free)
- Basic ability to create files and folders

---

## 🚀 **Step 1: Create GitHub Pages Repository**

### 1.1 Create New Repository

1. **Go to [GitHub](https://github.com)**
2. **Sign in** to your account
3. **Click the "+" icon** in top right → "New repository"
4. **Repository name**: `yourusername.github.io` 
   - ⚠️ **Important**: Replace `yourusername` with your actual GitHub username
   - Example: If your username is `john123`, name it `john123.github.io`
5. **Description**: `Tesla Fleet API domain for Powerwall automation`
6. **Set to Public** (required for GitHub Pages)
7. **Check "Add a README file"**
8. **Click "Create repository"**

### 1.2 Enable GitHub Pages

1. **Go to your new repository**
2. **Click "Settings" tab**
3. **Scroll down to "Pages" section** (left sidebar)
4. **Source**: Select "Deploy from a branch"
5. **Branch**: Select "main"
6. **Folder**: Select "/ (root)"
7. **Click "Save"**

Your site will be available at: `https://yourusername.github.io`

---

## 🔑 **Step 2: Generate Tesla Public Key**

### 2.1 Generate EC Private Key

**Option A: Using OpenSSL (Mac/Linux/WSL)**
```bash
# Generate private key
openssl ecparam -genkey -name prime256v1 -noout -out private_key.pem

# Generate public key
openssl ec -in private_key.pem -pubout -out public_key.pem
```

**Option B: Using Online Tool (Windows/Any)**
1. **Go to [Online EC Key Generator](https://8gwifi.org/ec.jsp)**
2. **Select Curve**: `prime256v1 (secp256r1)`
3. **Click "Generate Keys"**
4. **Copy the "Public Key" section** (starts with `-----BEGIN PUBLIC KEY-----`)

**Option C: Use Sample Key (For Testing)**
```
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE2I3Z+1Z8qJq2fQ7X5KoP9mR3sT8u
VwX7YzN2QcE4FpA6R8sL9Nc0bWxMjO5pT3qR7Ks9dX1nM4aP2vC8eG6HiQ==
-----END PUBLIC KEY-----
```
⚠️ **Security Note**: For production use, generate your own unique keys!

### 2.2 Save Your Keys

**Keep these files safe:**
- `private_key.pem` - Store securely (you'll need this later)
- `public_key.pem` - Upload to GitHub (next step)

---

## 📁 **Step 3: Create Required Directory Structure**

### 3.1 Create Directory Structure

In your GitHub repository, create this exact folder structure:

```
yourusername.github.io/
└── .well-known/
    └── appspecific/
        └── com.tesla.3p.public-key.pem
```

### 3.2 Create Folders via GitHub Web Interface

1. **Go to your repository** (`yourusername.github.io`)
2. **Click "Create new file"**
3. **Filename**: `.well-known/appspecific/com.tesla.3p.public-key.pem`
   - GitHub will automatically create the folders
4. **File content**: Paste your public key (including the `-----BEGIN` and `-----END` lines)
5. **Commit message**: `Add Tesla Fleet API public key`
6. **Click "Commit new file"**

### 3.3 Verify File Structure

Your repository should now look like:
```
📁 .well-known/
  📁 appspecific/
    📄 com.tesla.3p.public-key.pem
📄 README.md
```

---

## ✅ **Step 4: Verify Setup**

### 4.1 Test Public Access

1. **Wait 5-10 minutes** for GitHub Pages to deploy
2. **Visit**: `https://yourusername.github.io/.well-known/appspecific/com.tesla.3p.public-key.pem`
3. **You should see your public key** displayed in the browser

**Expected result:**
```
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE2I3Z+1Z8qJq2fQ7X5KoP9mR3sT8u
VwX7YzN2QcE4FpA6R8sL9Nc0bWxMjO5pT3qR7Ks9dX1nM4aP2vC8eG6HiQ==
-----END PUBLIC KEY-----
```

### 4.2 Test with curl (Optional)

```bash
curl https://yourusername.github.io/.well-known/appspecific/com.tesla.3p.public-key.pem
```

---

## 🔧 **Step 5: Update Repository README (Optional)**

Add this to your repository's README.md:

```markdown
# Tesla Fleet API Domain

This repository hosts the public key file required for Tesla Fleet API integration.

**Public Key URL**: https://yourusername.github.io/.well-known/appspecific/com.tesla.3p.public-key.pem

This domain is used for the [PW3Mate](https://github.com/yourusername/PW3Mate) Tesla Powerwall automation project.
```

---

## 🛡️ **Security Best Practices**

### 5.1 Private Key Security

**✅ DO:**
- Store private key in a secure password manager
- Back up the private key securely
- Use the private key only for Tesla Fleet API signing

**❌ DON'T:**
- Share the private key publicly
- Store the private key in GitHub
- Use the same key for multiple applications

### 5.2 Repository Security

**✅ DO:**
- Keep the repository public (required for GitHub Pages)
- Use a strong GitHub password and 2FA
- Regularly review repository access

**❌ DON'T:**
- Store any private credentials in this repository
- Grant unnecessary access to collaborators

---

## 🐛 **Troubleshooting**

### Common Issues

**Q: The public key URL returns 404**
- **A**: Wait 10-15 minutes for GitHub Pages to deploy, then try again

**Q: GitHub Pages not enabled**
- **A**: Go to Settings → Pages → Source → Select "Deploy from a branch"

**Q: Wrong file path**
- **A**: Ensure the exact path: `.well-known/appspecific/com.tesla.3p.public-key.pem`

**Q: File shows HTML instead of the key**
- **A**: The file extension should be `.pem`, not `.txt` or `.html`

### Advanced Troubleshooting

**Check GitHub Pages status:**
1. **Repository Settings** → **Pages**
2. **Look for green checkmark**: "Your site is published at..."
3. **If there's an error**, fix it and wait for re-deployment

**Force refresh deployment:**
1. **Make a small change** to any file
2. **Commit the change**
3. **Wait 5-10 minutes** for re-deployment

---

## 📝 **What's Next?**

Now that your GitHub domain is set up:

1. **Save your domain URL**: `https://yourusername.github.io`
2. **Keep your private key safe** - you'll need it for Tesla Fleet API registration
3. **Continue to**: [Tesla Fleet API Setup](01-tesla-fleet-api-setup.md)

---

## 🔗 **Related Documentation**

- [Tesla Fleet API Documentation](https://developer.tesla.com/docs/fleet-api)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [OpenSSL EC Key Generation](https://wiki.openssl.org/index.php/Command_Line_Elliptic_Curve_Operations)

---

**✅ Your GitHub domain is now ready for Tesla Fleet API integration!**

**Next Step**: [Tesla Fleet API Setup →](01-tesla-fleet-api-setup.md)