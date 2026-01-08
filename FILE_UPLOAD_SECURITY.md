# File Upload Security Guide

To maintain a secure environment for Bank.Ai, follow these best practices for handling file uploads.

## Backend Protections (Implemented)

### 1. File Signature Validation (Magic Numbers)
The system checks the first few bytes of every uploaded file to ensure the content matches the extension (e.g., a PDF must start with `%PDF-`). This prevents users from renaming malicious scripts (like `.php` or `.exe`) to `.pdf` to bypass filters.

### 2. Filename Sanitization
Filenames are sanitized to prevent Path Traversal attacks. All directory indicators (`../`) are removed, and a unique UUID is prepended to the filename to avoid overwriting existing files.

### 3. File Size Limits
A strict 10MB limit is enforced globally to prevent Denial of Service (DoS) attacks via disk exhaustion.

---

## Infrastructure Recommendations (Server Level)

### 1. Disable Execution in Uploads Directory
Ensure that the web server (Nginx/Apache/IIS) is configured to **not execute scripts** in the `uploads/` directory.

**Nginx Example:**
```nginx
location /uploads {
    location ~ \.(php|pl|py|jsp|sh|cgi)$ {
        deny all;
    }
}
```

### 2. Antivirus Integration
For high-traffic production environments, consider scanning all uploads with an antivirus like **ClamAV**.

### 3. Dedicated Storage
Store uploaded files on a dedicated volume or a cloud storage provider (like AWS S3 or Google Cloud Storage) to isolate the application server from potential file-based exploits.

### 4. Content Security Policy (CSP)
Use a strong CSP to prevent the browser from executing any scripts that might have been uploaded:
```http
Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none';
```
