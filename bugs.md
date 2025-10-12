# Bugs

- `MediaProcessor.__init__` references an undefined `file` variable when attempting MIME type checks, leading to a `NameError` during initialization and preventing file processing. The method also restricts uploads to only a few MIME types despite allowing more file extensions, which rejects legitimate formats. [backend/upload_handler.py lines 18-26]
- Admin API endpoints lack proper authorization checks; any authenticated user can perform administrative actions because role verification is missing. [backend/api.py lines 420-427]
- The application configuration uses hard-coded absolute paths for `UPLOAD_FOLDER` and `MEDIA_FOLDER`, making deployment on different systems difficult. [backend/app.py lines 23-24]
- The Flask app runs with `debug=True` in production, exposing sensitive information and reducing security. [backend/app.py line 67]
- Duplicate imports of `Limiter` and `get_remote_address` clutter the code and may cause confusion. [backend/app.py lines 1-7]
- File uploads lack malware scanning, leaving the system vulnerable to malicious files. [backend/upload_handler.py line 27-28]
